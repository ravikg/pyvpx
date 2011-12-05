import vpx

__author__ = 'Flier Lu'

class VpxError(Exception):
    def __init__(self, errno):
        Exception.__init__(self, vpx.vpx_codec_err_to_string(errno))
        self.errno = errno

    @staticmethod
    def check(errno):
        if errno != vpx.VPX_CODEC_OK:
            raise VpxError(errno)

class Image(object):
    def __init__(self, width, height, fmt=vpx.VPX_IMG_FMT_I420, data=None, align=1):
        self.img = vpx.vpx_image_t()

        if data:
            vpx.vpx_img_wrap(self.img, fmt, width, height, align, data)
        else:
            vpx.vpx_img_alloc(self.img, fmt, width, height, align)

    def flip(self):
        vpx.vpx_img_flip(self.img)

    def clear(self):
        vpx.vpx_img_clear(self.img)

    def free(self):
        vpx.vpx_img_free(self.img)

    @property
    def format(self):
        return self.img.fmt

    @property
    def width(self):
        return self.img.w

    @property
    def height(self):
        return self.img.h

    @property
    def bps(self):
        return self.img.bps

    @property
    def data(self):
        return vpx.vpx_img_get_data(self.img)
    
class Codec(object):
    def __init__(self, iface):
        self.iface = iface

    @property
    def name(self):
        "Return the name for a given interface"
        return vpx.vpx_codec_iface_name(self.iface)

    @property
    def caps(self):
        "Get the capabilities of an algorithm."
        return vpx.vpx_codec_get_caps(self.iface)

    @staticmethod
    def version():
        v = vpx.vpx_codec_version()
        return (((v>>16)&0xff), ((v>>8)&0xff), ((v>>0)&0xff),
                vpx.vpx_codec_version_str(),
                vpx.vpx_codec_version_extra_str(),
                vpx.vpx_codec_build_config())

class Context(object):
    def __init__(self, iface):
        self.iface = iface
        self.codec = vpx.vpx_codec_ctx_t()

    @property
    def err_msg(self):
        return vpx.vpx_codec_error(self.codec)

    @property
    def err_detail(self):
        return vpx.vpx_codec_error_detail(self.codec)

    def close(self):
        VpxError.check(vpx.vpx_codec_destroy(self.codec))

class Frames(object):
    def __init__(self, codec):
        self.codec = codec
        self.iter = vpx.vpx_codec_iter_alloc()

    def __iter__(self):
        return self

    def next(self):
        packet = vpx.vpx_codec_get_cx_data(self.codec, self.iter)

        if packet is None:
            raise StopIteration()

        return packet.kind, vpx.vpx_pkt_get_data(packet)

class Encoder(Context):
    Interface = Codec(vpx.vpx_codec_vp8_cx())

    def __init__(self, width, height):
        Context.__init__(self, vpx.vpx_codec_vp8_cx())

        self.cfg = vpx.vpx_codec_enc_cfg_t()

        VpxError.check(vpx.vpx_codec_enc_config_default(self.iface, self.cfg, 0))

        self.cfg.rc_target_bitrate = width * height * self.cfg.rc_target_bitrate / self.cfg.g_w / self.cfg.g_h
        self.cfg.g_w = width
        self.cfg.g_h = height

        VpxError.check(vpx.vpx_codec_enc_init_ver(self.codec, self.iface, self.cfg, 0, vpx.VPX_ENCODER_ABI_VERSION))

    @property
    def width(self):
        return self.cfg.g_w

    @property
    def height(self):
        return self.cfg.g_h

    @property
    def config(self):
        return self.cfg

    @config.setter
    def config(self, cfg):
        self.cfg = cfg

        VpxError.check(vpx.vpx_codec_enc_config_set(self.codec, self.cfg))

        return self.cfg

    def encode(self, img, pts, duration=1, flags=0, deadline=vpx.VPX_DL_REALTIME):
        VpxError.check(vpx.vpx_codec_encode(self.codec, img.img, pts, duration, flags, deadline));

        return Frames(self.codec)
    