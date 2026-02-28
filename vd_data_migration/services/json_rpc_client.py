import json
import logging
import socket
import urllib.error
import urllib.request

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class JsonRpcClient:
    """JSON-RPC 2.0 client for communicating with a remote Odoo instance.

    Uses only Python stdlib (urllib.request + json) — no external dependencies.

    Endpoints used on the source instance:
        Auth:  POST /web/session/authenticate
        Calls: POST /web/dataset/call_kw
    """

    TIMEOUT = 30  # seconds

    def __init__(self, url: str, db: str, login: str, password: str) -> None:
        """Initialize the client with connection parameters.

        Args:
            url: Base URL of the source Odoo instance.
            db: Database name on the source instance.
            login: Username for authentication.
            password: Password for authentication.
        """
        self.url = url.rstrip('/')
        self.db = db
        self.login = login
        self.password = password
        self._session_id: str | None = None
        self._uid: int | None = None

    def authenticate(self) -> str:
        """Authenticate against the source Odoo instance.

        Sends POST /web/session/authenticate and stores the session_id
        from the response cookie.

        Returns:
            str: The session_id obtained from the server.

        Raises:
            UserError: If authentication fails or the server is unreachable.
        """
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 1,
            'params': {
                'db': self.db,
                'login': self.login,
                'password': self.password,
            },
        }
        endpoint = f'{self.url}/web/session/authenticate'
        _logger.info('Authenticating at %s  db=%s  login=%s', self.url, self.db, self.login)

        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers={'Content-Type': 'application/json'},
            )
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                raw = resp.read()
                cookie_header = resp.headers.get('Set-Cookie', '')

            result = json.loads(raw)
            self._handle_rpc_error(result, 'authenticate')

            uid = result.get('result', {}).get('uid')
            if not uid:
                raise UserError('Authentication failed: invalid login or password.')

            # Parse session_id from Set-Cookie header
            for part in cookie_header.split(';'):
                part = part.strip()
                if part.startswith('session_id='):
                    self._session_id = part.split('=', 1)[1]
                    break

            self._uid = uid
            _logger.info('Authenticated successfully: uid=%s', uid)
            return self._session_id or ''

        except UserError:
            raise
        except socket.timeout:
            _logger.error('Timeout connecting to %s', self.url)
            raise UserError(f'Server not reachable: connection timed out ({self.url}).')
        except urllib.error.URLError as exc:
            _logger.error('URLError connecting to %s: %s', self.url, exc)
            raise UserError(f'Server not reachable: {exc.reason}.')
        except Exception as exc:
            _logger.error('Unexpected error during authenticate: %s', exc)
            raise UserError(f'Authentication error: {exc}')

    def _call_kw(self, model: str, method: str, args: list, kwargs: dict) -> any:
        """Execute a JSON-RPC call_kw request on the source instance.

        Args:
            model: Odoo model name (e.g. 'res.partner').
            method: ORM method name (e.g. 'search_read').
            args: Positional arguments list.
            kwargs: Keyword arguments dict.

        Returns:
            The 'result' value from the JSON-RPC response.

        Raises:
            UserError: On network error or JSON-RPC error response.
        """
        if not self._session_id:
            raise UserError('Not authenticated. Call authenticate() first.')

        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'id': 1,
            'params': {
                'model': model,
                'method': method,
                'args': args,
                'kwargs': kwargs,
            },
        }
        endpoint = f'{self.url}/web/dataset/call_kw'

        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': f'session_id={self._session_id}',
                },
            )
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                raw = resp.read()

            result = json.loads(raw)
            self._handle_rpc_error(result, f'{model}.{method}')
            return result.get('result')

        except UserError:
            raise
        except socket.timeout:
            _logger.error('Timeout on %s.%s', model, method)
            raise UserError('Server not reachable: connection timed out.')
        except urllib.error.URLError as exc:
            _logger.error('URLError on %s.%s: %s', model, method, exc)
            raise UserError(f'Network error: {exc.reason}.')
        except Exception as exc:
            _logger.error('Unexpected error on %s.%s: %s', model, method, exc)
            raise UserError(f'RPC error: {exc}')

    def model_exists(self, model: str) -> bool:
        """Check whether a model exists on the source instance.

        Args:
            model: Technical model name (e.g. 'res.partner').

        Returns:
            bool: True if the model exists.
        """
        count = self._call_kw(
            'ir.model',
            'search_count',
            [[('model', '=', model)]],
            {},
        )
        _logger.info('model_exists(%s) = %s', model, bool(count))
        return bool(count)

    def fields_get(self, model: str) -> dict:
        """Fetch field metadata for a model from the source instance.

        Args:
            model: Technical model name.

        Returns:
            dict: Mapping field_name -> {string, type, relation}.
        """
        result = self._call_kw(
            model,
            'fields_get',
            [],
            {'attributes': ['string', 'type', 'relation']},
        )
        fields = result or {}
        _logger.info('fields_get(%s): %d fields', model, len(fields))
        return fields

    def search_count(self, model: str) -> int:
        """Return total record count for a model on the source instance.

        Args:
            model: Technical model name.

        Returns:
            int: Number of records.
        """
        count = self._call_kw(model, 'search_count', [[]], {}) or 0
        _logger.info('search_count(%s) = %d', model, count)
        return count

    def search_read(self, model: str, fields: list, offset: int, limit: int) -> list:
        """Read a batch of records from the source instance.

        Args:
            model: Technical model name.
            fields: List of field names to fetch.
            offset: Offset for pagination.
            limit: Maximum number of records to return (always 100 per NFR-04).

        Returns:
            list[dict]: List of record dicts. Empty list signals end of data.
        """
        records = self._call_kw(
            model,
            'search_read',
            [[]],
            {'fields': fields, 'offset': offset, 'limit': limit},
        ) or []
        _logger.info(
            'search_read(%s, offset=%d, limit=%d): got %d records',
            model, offset, limit, len(records),
        )
        return records

    # ── Internal helpers ──────────────────────────────────────────────────

    @staticmethod
    def _handle_rpc_error(response: dict, context: str) -> None:
        """Raise UserError if the JSON-RPC response contains an error field.

        Args:
            response: Parsed JSON-RPC response dict.
            context: Human-readable context for the error message.

        Raises:
            UserError: If response contains an 'error' key.
        """
        error = response.get('error')
        if error:
            msg = (
                error.get('data', {}).get('message')
                or error.get('message')
                or str(error)
            )
            _logger.error('RPC error in %s: %s', context, msg)
            raise UserError(f'Remote error ({context}): {msg}')
