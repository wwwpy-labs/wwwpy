import pytest

from wwwpy.common.rpc2.encoder_decoder import JsonEncoderDecoder


def test_encoder_buffer():
    target = JsonEncoderDecoder()

    enc = target.encoder()

    enc.encode('ciao', str)
    enc.encode(123, int)

    assert enc.buffer

    dec = target.decoder(enc.buffer)

    assert 'ciao' == dec.decode(str)
    assert 123 == dec.decode(int)

    with pytest.raises(Exception):
        dec.decode(str)
