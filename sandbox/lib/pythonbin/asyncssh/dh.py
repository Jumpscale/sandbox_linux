# Copyright (c) 2013-2018 by Ron Frederick <ronf@timeheart.net>.
# All rights reserved.
#
# This program and the accompanying materials are made available under
# the terms of the Eclipse Public License v1.0 which accompanies this
# distribution and is available at:
#
#     http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
#     Ron Frederick - initial implementation, API, and documentation

"""SSH Diffie-Hellman key exchange handlers"""

from hashlib import sha1, sha256, sha512

from .constants import DEFAULT_LANG
from .constants import DISC_KEY_EXCHANGE_FAILED, DISC_PROTOCOL_ERROR
from .gss import GSSError
from .kex import Kex, register_kex_alg, register_gss_kex_alg
from .misc import DisconnectError, get_symbol_names, randrange
from .packet import Boolean, MPInt, String, UInt32


# pylint: disable=bad-whitespace,line-too-long

# SSH KEX DH message values
MSG_KEXDH_INIT             = 30
MSG_KEXDH_REPLY            = 31

# SSH KEX DH group exchange message values
MSG_KEX_DH_GEX_REQUEST_OLD = 30
MSG_KEX_DH_GEX_GROUP       = 31
MSG_KEX_DH_GEX_INIT        = 32
MSG_KEX_DH_GEX_REPLY       = 33
MSG_KEX_DH_GEX_REQUEST     = 34

# SSH KEXGSS message value
MSG_KEXGSS_INIT            = 30
MSG_KEXGSS_CONTINUE        = 31
MSG_KEXGSS_COMPLETE        = 32
MSG_KEXGSS_HOSTKEY         = 33
MSG_KEXGSS_ERROR           = 34
MSG_KEXGSS_GROUPREQ        = 40
MSG_KEXGSS_GROUP           = 41

# SSH KEX group exchange key sizes
KEX_DH_GEX_MIN_SIZE        = 1024
KEX_DH_GEX_PREFERRED_SIZE  = 2048
KEX_DH_GEX_MAX_SIZE        = 8192

# SSH Diffie-Hellman group 1 parameters
_group1_g = 2
_group1_p = 0xffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd129024e088a67cc74020bbea63b139b22514a08798e3404ddef9519b3cd3a431b302b0a6df25f14374fe1356d6d51c245e485b576625e7ec6f44c42e9a637ed6b0bff5cb6f406b7edee386bfb5a899fa5ae9f24117c4b1fe649286651ece65381ffffffffffffffff

# SSH Diffie-Hellman group 14 parameters
_group14_g = 2
_group14_p = 0xffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd129024e088a67cc74020bbea63b139b22514a08798e3404ddef9519b3cd3a431b302b0a6df25f14374fe1356d6d51c245e485b576625e7ec6f44c42e9a637ed6b0bff5cb6f406b7edee386bfb5a899fa5ae9f24117c4b1fe649286651ece45b3dc2007cb8a163bf0598da48361c55d39a69163fa8fd24cf5f83655d23dca3ad961c62f356208552bb9ed529077096966d670c354e4abc9804f1746c08ca18217c32905e462e36ce3be39e772c180e86039b2783a2ec07a28fb5c55df06f4c52c9de2bcbf6955817183995497cea956ae515d2261898fa051015728e5a8aacaa68ffffffffffffffff

# SSH Diffie-Hellman group 15 parameters
_group15_g = 2
_group15_p = 0xffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd129024e088a67cc74020bbea63b139b22514a08798e3404ddef9519b3cd3a431b302b0a6df25f14374fe1356d6d51c245e485b576625e7ec6f44c42e9a637ed6b0bff5cb6f406b7edee386bfb5a899fa5ae9f24117c4b1fe649286651ece45b3dc2007cb8a163bf0598da48361c55d39a69163fa8fd24cf5f83655d23dca3ad961c62f356208552bb9ed529077096966d670c354e4abc9804f1746c08ca18217c32905e462e36ce3be39e772c180e86039b2783a2ec07a28fb5c55df06f4c52c9de2bcbf6955817183995497cea956ae515d2261898fa051015728e5a8aaac42dad33170d04507a33a85521abdf1cba64ecfb850458dbef0a8aea71575d060c7db3970f85a6e1e4c7abf5ae8cdb0933d71e8c94e04a25619dcee3d2261ad2ee6bf12ffa06d98a0864d87602733ec86a64521f2b18177b200cbbe117577a615d6c770988c0bad946e208e24fa074e5ab3143db5bfce0fd108e4b82d120a93ad2caffffffffffffffff

# SSH Diffie-Hellman group 16 parameters
_group16_g = 2
_group16_p = 0xffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd129024e088a67cc74020bbea63b139b22514a08798e3404ddef9519b3cd3a431b302b0a6df25f14374fe1356d6d51c245e485b576625e7ec6f44c42e9a637ed6b0bff5cb6f406b7edee386bfb5a899fa5ae9f24117c4b1fe649286651ece45b3dc2007cb8a163bf0598da48361c55d39a69163fa8fd24cf5f83655d23dca3ad961c62f356208552bb9ed529077096966d670c354e4abc9804f1746c08ca18217c32905e462e36ce3be39e772c180e86039b2783a2ec07a28fb5c55df06f4c52c9de2bcbf6955817183995497cea956ae515d2261898fa051015728e5a8aaac42dad33170d04507a33a85521abdf1cba64ecfb850458dbef0a8aea71575d060c7db3970f85a6e1e4c7abf5ae8cdb0933d71e8c94e04a25619dcee3d2261ad2ee6bf12ffa06d98a0864d87602733ec86a64521f2b18177b200cbbe117577a615d6c770988c0bad946e208e24fa074e5ab3143db5bfce0fd108e4b82d120a92108011a723c12a787e6d788719a10bdba5b2699c327186af4e23c1a946834b6150bda2583e9ca2ad44ce8dbbbc2db04de8ef92e8efc141fbecaa6287c59474e6bc05d99b2964fa090c3a2233ba186515be7ed1f612970cee2d7afb81bdd762170481cd0069127d5b05aa993b4ea988d8fddc186ffb7dc90a6c08f4df435c934063199ffffffffffffffff

# SSH Diffie-Hellman group 17 parameters
_group17_g = 2
_group17_p = 0xffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd129024e088a67cc74020bbea63b139b22514a08798e3404ddef9519b3cd3a431b302b0a6df25f14374fe1356d6d51c245e485b576625e7ec6f44c42e9a637ed6b0bff5cb6f406b7edee386bfb5a899fa5ae9f24117c4b1fe649286651ece45b3dc2007cb8a163bf0598da48361c55d39a69163fa8fd24cf5f83655d23dca3ad961c62f356208552bb9ed529077096966d670c354e4abc9804f1746c08ca18217c32905e462e36ce3be39e772c180e86039b2783a2ec07a28fb5c55df06f4c52c9de2bcbf6955817183995497cea956ae515d2261898fa051015728e5a8aaac42dad33170d04507a33a85521abdf1cba64ecfb850458dbef0a8aea71575d060c7db3970f85a6e1e4c7abf5ae8cdb0933d71e8c94e04a25619dcee3d2261ad2ee6bf12ffa06d98a0864d87602733ec86a64521f2b18177b200cbbe117577a615d6c770988c0bad946e208e24fa074e5ab3143db5bfce0fd108e4b82d120a92108011a723c12a787e6d788719a10bdba5b2699c327186af4e23c1a946834b6150bda2583e9ca2ad44ce8dbbbc2db04de8ef92e8efc141fbecaa6287c59474e6bc05d99b2964fa090c3a2233ba186515be7ed1f612970cee2d7afb81bdd762170481cd0069127d5b05aa993b4ea988d8fddc186ffb7dc90a6c08f4df435c93402849236c3fab4d27c7026c1d4dcb2602646dec9751e763dba37bdf8ff9406ad9e530ee5db382f413001aeb06a53ed9027d831179727b0865a8918da3edbebcf9b14ed44ce6cbaced4bb1bdb7f1447e6cc254b332051512bd7af426fb8f401378cd2bf5983ca01c64b92ecf032ea15d1721d03f482d7ce6e74fef6d55e702f46980c82b5a84031900b1c9e59e7c97fbec7e8f323a97a7e36cc88be0f1d45b7ff585ac54bd407b22b4154aacc8f6d7ebf48e1d814cc5ed20f8037e0a79715eef29be32806a1d58bb7c5da76f550aa3d8a1fbff0eb19ccb1a313d55cda56c9ec2ef29632387fe8d76e3c0468043e8f663f4860ee12bf2d5b0b7474d6e694f91e6dcc4024ffffffffffffffff

# SSH Diffie-Hellman group 18 parameters
_group18_g = 2
_group18_p = 0xffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd129024e088a67cc74020bbea63b139b22514a08798e3404ddef9519b3cd3a431b302b0a6df25f14374fe1356d6d51c245e485b576625e7ec6f44c42e9a637ed6b0bff5cb6f406b7edee386bfb5a899fa5ae9f24117c4b1fe649286651ece45b3dc2007cb8a163bf0598da48361c55d39a69163fa8fd24cf5f83655d23dca3ad961c62f356208552bb9ed529077096966d670c354e4abc9804f1746c08ca18217c32905e462e36ce3be39e772c180e86039b2783a2ec07a28fb5c55df06f4c52c9de2bcbf6955817183995497cea956ae515d2261898fa051015728e5a8aaac42dad33170d04507a33a85521abdf1cba64ecfb850458dbef0a8aea71575d060c7db3970f85a6e1e4c7abf5ae8cdb0933d71e8c94e04a25619dcee3d2261ad2ee6bf12ffa06d98a0864d87602733ec86a64521f2b18177b200cbbe117577a615d6c770988c0bad946e208e24fa074e5ab3143db5bfce0fd108e4b82d120a92108011a723c12a787e6d788719a10bdba5b2699c327186af4e23c1a946834b6150bda2583e9ca2ad44ce8dbbbc2db04de8ef92e8efc141fbecaa6287c59474e6bc05d99b2964fa090c3a2233ba186515be7ed1f612970cee2d7afb81bdd762170481cd0069127d5b05aa993b4ea988d8fddc186ffb7dc90a6c08f4df435c93402849236c3fab4d27c7026c1d4dcb2602646dec9751e763dba37bdf8ff9406ad9e530ee5db382f413001aeb06a53ed9027d831179727b0865a8918da3edbebcf9b14ed44ce6cbaced4bb1bdb7f1447e6cc254b332051512bd7af426fb8f401378cd2bf5983ca01c64b92ecf032ea15d1721d03f482d7ce6e74fef6d55e702f46980c82b5a84031900b1c9e59e7c97fbec7e8f323a97a7e36cc88be0f1d45b7ff585ac54bd407b22b4154aacc8f6d7ebf48e1d814cc5ed20f8037e0a79715eef29be32806a1d58bb7c5da76f550aa3d8a1fbff0eb19ccb1a313d55cda56c9ec2ef29632387fe8d76e3c0468043e8f663f4860ee12bf2d5b0b7474d6e694f91e6dbe115974a3926f12fee5e438777cb6a932df8cd8bec4d073b931ba3bc832b68d9dd300741fa7bf8afc47ed2576f6936ba424663aab639c5ae4f5683423b4742bf1c978238f16cbe39d652de3fdb8befc848ad922222e04a4037c0713eb57a81a23f0c73473fc646cea306b4bcbc8862f8385ddfa9d4b7fa2c087e879683303ed5bdd3a062b3cf5b3a278a66d2a13f83f44f82ddf310ee074ab6a364597e899a0255dc164f31cc50846851df9ab48195ded7ea1b1d510bd7ee74d73faf36bc31ecfa268359046f4eb879f924009438b481c6cd7889a002ed5ee382bc9190da6fc026e479558e4475677e9aa9e3050e2765694dfc81f56e880b96e7160c980dd98edd3dfffffffffffffffff

_dh_gex_groups = ((1024, _group1_g,  _group1_p),
                  (2048, _group14_g, _group14_p),
                  (3072, _group15_g, _group15_p),
                  (4096, _group16_g, _group16_p),
                  (6144, _group17_g, _group17_p),
                  (8192, _group18_g, _group18_p))

# pylint: enable=bad-whitespace,line-too-long

# Short variable names are used here, matching names in the spec
# pylint: disable=invalid-name


class _KexDHBase(Kex):
    """Abstract base class for Diffie-Hellman key exchange"""

    _init_type = None
    _reply_type = None

    def __init__(self, alg, conn, hash_alg):
        super().__init__(alg, conn, hash_alg)

        self._g = None
        self._p = None
        self._q = None
        self._x = None
        self._e = None
        self._f = None
        self._gex_data = b''

    def _init_group(self, g, p):
        """Initialize DH group parameters"""

        self._g = g
        self._p = p
        self._q = (p - 1) // 2

    def _compute_hash(self, host_key_data, k):
        """Compute a hash of key information associated with the connection"""

        hash_obj = self._hash_alg()
        hash_obj.update(self._conn.get_hash_prefix())
        hash_obj.update(String(host_key_data))
        hash_obj.update(self._gex_data)
        hash_obj.update(MPInt(self._e))
        hash_obj.update(MPInt(self._f))
        hash_obj.update(MPInt(k))
        return hash_obj.digest()

    def _send_init(self):
        """Send a DH init message"""

        self.send_packet(self._init_type, MPInt(self._e))

    def _send_reply(self, key_data, sig):
        """Send a DH reply message"""

        self.send_packet(self._reply_type, String(key_data),
                         MPInt(self._f), String(sig))

    def _perform_init(self):
        """Compute e and send init message"""

        self._x = randrange(2, self._q)
        self._e = pow(self._g, self._x, self._p)

        self._send_init()

    def _perform_reply(self, key, key_data):
        """Compute f and send reply message"""

        if not 1 <= self._e < self._p:
            raise DisconnectError(DISC_PROTOCOL_ERROR, 'Kex DH e out of range')

        y = randrange(2, self._q)
        self._f = pow(self._g, y, self._p)

        k = pow(self._e, y, self._p)

        if k < 1: # pragma: no cover, shouldn't be possible with valid p
            raise DisconnectError(DISC_PROTOCOL_ERROR, 'Kex DH k out of range')

        h = self._compute_hash(key_data, k)
        self._send_reply(key_data, key.sign(h))

        self._conn.send_newkeys(k, h)

    def _verify_reply(self, key, key_data, sig):
        """Verify a DH reply message"""

        if not 1 <= self._f < self._p:
            raise DisconnectError(DISC_PROTOCOL_ERROR, 'Kex DH f out of range')

        k = pow(self._f, self._x, self._p)

        if k < 1: # pragma: no cover, shouldn't be possible with valid p
            raise DisconnectError(DISC_PROTOCOL_ERROR, 'Kex DH k out of range')

        h = self._compute_hash(key_data, k)

        if not key.verify(h, sig):
            raise DisconnectError(DISC_KEY_EXCHANGE_FAILED,
                                  'Key exchange hash mismatch')

        self._conn.send_newkeys(k, h)

    def _process_init(self, pkttype, pktid, packet):
        """Process a DH init message"""

        # pylint: disable=unused-argument

        if self._conn.is_client() or not self._p:
            raise DisconnectError(DISC_PROTOCOL_ERROR,
                                  'Unexpected kex init msg')

        self._e = packet.get_mpint()
        packet.check_end()

        host_key = self._conn.get_server_host_key()
        self._perform_reply(host_key, host_key.public_data)

    def _process_reply(self, pkttype, pktid, packet):
        """Process a DH reply message"""

        # pylint: disable=unused-argument

        if self._conn.is_server() or not self._p:
            raise DisconnectError(DISC_PROTOCOL_ERROR,
                                  'Unexpected kex reply msg')

        host_key_data = packet.get_string()
        self._f = packet.get_mpint()
        sig = packet.get_string()
        packet.check_end()

        host_key = self._conn.validate_server_host_key(host_key_data)
        self._verify_reply(host_key, host_key_data, sig)

    def start(self):
        """Start DH key exchange"""

        self._perform_init()


class _KexDH(_KexDHBase):
    """Handler for Diffie-Hellman key exchange"""

    _handler_names = get_symbol_names(globals(), 'MSG_KEXDH_')

    _init_type = MSG_KEXDH_INIT
    _reply_type = MSG_KEXDH_REPLY

    def __init__(self, alg, conn, hash_alg, g, p):
        super().__init__(alg, conn, hash_alg)

        self._init_group(g, p)

    _packet_handlers = {
        MSG_KEXDH_INIT:     _KexDHBase._process_init,
        MSG_KEXDH_REPLY:    _KexDHBase._process_reply
    }


class _KexDHGex(_KexDHBase):
    """Handler for Diffie-Hellman group exchange"""

    _handler_names = get_symbol_names(globals(), 'MSG_KEX_DH_GEX_')

    _init_type = MSG_KEX_DH_GEX_INIT
    _reply_type = MSG_KEX_DH_GEX_REPLY
    _request_type = MSG_KEX_DH_GEX_REQUEST
    _group_type = MSG_KEX_DH_GEX_GROUP

    def __init__(self, alg, conn, hash_alg, preferred_size=None, max_size=None):
        super().__init__(alg, conn, hash_alg)

        self._pref_size = preferred_size
        self._max_size = max_size

    def _send_request(self):
        """Send a DH gex request message"""

        if self._pref_size and not self._max_size:
            # Send old request message for unit test
            pkttype = MSG_KEX_DH_GEX_REQUEST_OLD
            args = UInt32(self._pref_size)
        else:
            pkttype = self._request_type
            args = (UInt32(KEX_DH_GEX_MIN_SIZE) +
                    UInt32(self._pref_size or KEX_DH_GEX_PREFERRED_SIZE) +
                    UInt32(self._max_size or KEX_DH_GEX_MAX_SIZE))

        self._gex_data = args
        self.send_packet(pkttype, args)

    def _process_request(self, pkttype, pktid, packet):
        """Process a DH gex request message"""

        # pylint: disable=unused-argument

        if self._conn.is_client():
            raise DisconnectError(DISC_PROTOCOL_ERROR,
                                  'Unexpected kex request msg')

        self._gex_data = packet.get_remaining_payload()

        if pkttype == MSG_KEX_DH_GEX_REQUEST_OLD:
            preferred_size = packet.get_uint32()
            max_size = KEX_DH_GEX_MAX_SIZE
        else:
            _ = packet.get_uint32()
            preferred_size = packet.get_uint32()
            max_size = packet.get_uint32()

        packet.check_end()

        g, p = _group1_g, _group1_p

        for gex_size, gex_g, gex_p in _dh_gex_groups:
            if gex_size > max_size:
                break
            else:
                g, p = gex_g, gex_p

                if gex_size >= preferred_size:
                    break

        self._init_group(g, p)
        self._gex_data += MPInt(p) + MPInt(g)
        self.send_packet(self._group_type, MPInt(p), MPInt(g))

    def _process_group(self, pkttype, pktid, packet):
        """Process a DH gex group message"""

        # pylint: disable=unused-argument

        if self._conn.is_server():
            raise DisconnectError(DISC_PROTOCOL_ERROR,
                                  'Unexpected kex group msg')

        p = packet.get_mpint()
        g = packet.get_mpint()
        packet.check_end()

        self._init_group(g, p)
        self._gex_data += MPInt(p) + MPInt(g)
        self._perform_init()

    def start(self):
        """Start DH group exchange"""

        self._send_request()

    _packet_handlers = {
        MSG_KEX_DH_GEX_REQUEST_OLD: _process_request,
        MSG_KEX_DH_GEX_GROUP:       _process_group,
        MSG_KEX_DH_GEX_INIT:        _KexDHBase._process_init,
        MSG_KEX_DH_GEX_REPLY:       _KexDHBase._process_reply,
        MSG_KEX_DH_GEX_REQUEST:     _process_request
    }


class _KexGSSBase(_KexDHBase):
    """Handler for GSS key exchange"""

    def __init__(self, alg, conn, hash_alg, *args):
        super().__init__(alg, conn, hash_alg, *args)

        self._gss = conn.get_gss_context()
        self._token = None
        self._host_key_data = b''
        self._got_error = False

    def _check_secure(self):
        """Check that GSS context is secure enough for key exchange"""

        if (not self._gss.provides_mutual_auth or
                not self._gss.provides_integrity):
            raise DisconnectError(DISC_PROTOCOL_ERROR,
                                  'GSS context not secure')

    def _send_init(self):
        """Send a GSS init message"""

        if not self._token:
            raise DisconnectError(DISC_PROTOCOL_ERROR,
                                  'Empty GSS token in init')

        self.send_packet(MSG_KEXGSS_INIT, String(self._token), MPInt(self._e))

    def _send_reply(self, key_data, sig):
        """Send a GSS reply message"""

        if self._token:
            token_data = Boolean(True) + String(self._token)
        else:
            token_data = Boolean(False)

        self.send_packet(MSG_KEXGSS_COMPLETE, MPInt(self._f),
                         String(sig), token_data)

    def _send_continue(self):
        """Send a GSS continue message"""

        if not self._token:
            raise DisconnectError(DISC_PROTOCOL_ERROR,
                                  'Empty GSS token in continue')

        self.send_packet(MSG_KEXGSS_CONTINUE, String(self._token))

    def _process_token(self, token=None):
        """Process a GSS token"""

        try:
            self._token = self._gss.step(token)
        except GSSError as exc:
            if self._conn.is_server():
                self.send_packet(MSG_KEXGSS_ERROR, UInt32(exc.maj_code),
                                 UInt32(exc.min_code), String(str(exc)),
                                 String(DEFAULT_LANG))

            if exc.token:
                self.send_packet(MSG_KEXGSS_CONTINUE, String(exc.token))

            raise DisconnectError(DISC_KEY_EXCHANGE_FAILED, str(exc))

    def _process_init(self, pkttype, pktid, packet):
        """Process a GSS init message"""

        # pylint: disable=unused-argument

        if self._conn.is_client() or not self._p:
            raise DisconnectError(DISC_PROTOCOL_ERROR,
                                  'Unexpected kexgss init msg')

        token = packet.get_string()
        self._e = packet.get_mpint()
        packet.check_end()

        host_key = self._conn.get_server_host_key()

        if host_key:
            self._host_key_data = host_key.public_data
            self.send_packet(MSG_KEXGSS_HOSTKEY, String(self._host_key_data))
        else:
            self._host_key_data = b''

        self._process_token(token)

        if self._gss.complete:
            self._check_secure()
            self._perform_reply(self._gss, self._host_key_data)
            self._conn.enable_gss_kex_auth()
        else:
            self._send_continue()

    def _process_continue(self, pkttype, pktid, packet):
        """Process a GSS continue message"""

        # pylint: disable=unused-argument

        token = packet.get_string()
        packet.check_end()

        if self._conn.is_client() and self._gss.complete:
            raise DisconnectError(DISC_PROTOCOL_ERROR,
                                  'Unexpected kexgss continue msg')

        self._process_token(token)

        if self._conn.is_server() and self._gss.complete:
            self._check_secure()
            self._perform_reply(self._gss, self._host_key_data)
        else:
            self._send_continue()

    def _process_complete(self, pkttype, pktid, packet):
        """Process a GSS complete message"""

        # pylint: disable=unused-argument

        if self._conn.is_server():
            raise DisconnectError(DISC_PROTOCOL_ERROR,
                                  'Unexpected kexgss complete msg')

        self._f = packet.get_mpint()
        mic = packet.get_string()
        token_present = packet.get_boolean()
        token = packet.get_string() if token_present else None
        packet.check_end()

        if token:
            if self._gss.complete:
                raise DisconnectError(DISC_PROTOCOL_ERROR,
                                      'Non-empty token after complete')

            self._process_token(token)

            if self._token:
                raise DisconnectError(DISC_PROTOCOL_ERROR,
                                      'Non-empty token after complete')

        if not self._gss.complete:
            raise DisconnectError(DISC_PROTOCOL_ERROR,
                                  'GSS exchange failed to complete')

        self._check_secure()
        self._verify_reply(self._gss, self._host_key_data, mic)
        self._conn.enable_gss_kex_auth()

    def _process_hostkey(self, pkttype, pktid, packet):
        """Process a GSS hostkey message"""

        # pylint: disable=unused-argument

        self._host_key_data = packet.get_string()
        packet.check_end()

    def _process_error(self, pkttype, pktid, packet):
        """Process a GSS error message"""

        # pylint: disable=unused-argument

        if self._conn.is_server():
            raise DisconnectError(DISC_PROTOCOL_ERROR,
                                  'Unexpected kexgss error msg')

        _ = packet.get_uint32()         # major_status
        _ = packet.get_uint32()         # minor_status
        msg = packet.get_string()
        _ = packet.get_string()         # lang
        packet.check_end()

        self._conn.logger.warning('GSS error: %s',
                                  msg.decode('utf-8', errors='ignore'))
        self._got_error = True

    def start(self):
        """Start GSS key or group exchange"""

        self._process_token()
        super().start()


class _KexGSS(_KexGSSBase, _KexDH):
    """Handler for GSS key exchange"""

    _handler_names = get_symbol_names(globals(), 'MSG_KEXGSS_')

    _packet_handlers = {
        MSG_KEXGSS_INIT:     _KexGSSBase._process_init,
        MSG_KEXGSS_CONTINUE: _KexGSSBase._process_continue,
        MSG_KEXGSS_COMPLETE: _KexGSSBase._process_complete,
        MSG_KEXGSS_HOSTKEY:  _KexGSSBase._process_hostkey,
        MSG_KEXGSS_ERROR:    _KexGSSBase._process_error
    }


class _KexGSSGex(_KexGSSBase, _KexDHGex):
    """Handler for GSS group exchange"""

    _handler_names = get_symbol_names(globals(), 'MSG_KEXGSS_')

    _request_type = MSG_KEXGSS_GROUPREQ
    _group_type = MSG_KEXGSS_GROUP

    _packet_handlers = {
        MSG_KEXGSS_INIT:     _KexGSSBase._process_init,
        MSG_KEXGSS_CONTINUE: _KexGSSBase._process_continue,
        MSG_KEXGSS_COMPLETE: _KexGSSBase._process_complete,
        MSG_KEXGSS_HOSTKEY:  _KexGSSBase._process_hostkey,
        MSG_KEXGSS_ERROR:    _KexGSSBase._process_error,
        MSG_KEXGSS_GROUPREQ: _KexDHGex._process_request,
        MSG_KEXGSS_GROUP:    _KexDHGex._process_group
    }


# pylint: disable=bad-whitespace

for _name, _hash_alg in ((b'sha256', sha256), (b'sha1', sha1)):
    register_kex_alg(b'diffie-hellman-group-exchange-' + _name,
                     _KexDHGex, _hash_alg)
    register_gss_kex_alg(b'gss-gex-' + _name, _KexGSSGex, _hash_alg)

for _name, _hash_alg, _g, _p in (
        (b'group1-sha1',    sha1,   _group1_g,  _group1_p),
        (b'group14-sha1',   sha1,   _group14_g, _group14_p),
        (b'group14-sha256', sha256, _group14_g, _group14_p),
        (b'group15-sha512', sha512, _group15_g, _group15_p),
        (b'group16-sha512', sha512, _group16_g, _group16_p),
        (b'group17-sha512', sha512, _group17_g, _group17_p),
        (b'group18-sha512', sha512, _group18_g, _group18_p)):
    register_kex_alg(b'diffie-hellman-' + _name, _KexDH, _hash_alg, _g, _p)
    register_gss_kex_alg(b'gss-' + _name, _KexGSS, _hash_alg, _g, _p)
