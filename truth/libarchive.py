from config_truth import GroundTruthExtractor




class Libxml2GroundTruth(GroundTruthExtractor):
    def extract(self, config_h, name, src_dir):
        flags = set()
        flags.add(("LIBSSH2_OPENSSL", "TRUE")



| Configure Flag                             | Macro(s) Affected | Description                        |
| ------------------------------------------ | ----------------- | ---------------------------------- |
| `--with-zlib` / `--without-zlib`           | `HAVE_LIBZ`       | Enable/disable zlib (gzip) support |
| `--with-bz2` / `--without-bz2`             | `HAVE_LIBBZ2`     | Enable/disable bzip2 support       |
| `--with-lzma` / `--without-lzma`           | `HAVE_LIBLZMA`    | Enable/disable xz/lzma support     |
| `--with-lz4` / `--without-lz4`             | `HAVE_LIBLZ4`     | Enable/disable lz4 support         |
| `--with-zstd` / `--without-zstd`           | `HAVE_LIBZSTD`    | Enable/disable zstd support        |
| `--with-openssl` / `--without-openssl`     | `HAVE_OPENSSL`    | Use OpenSSL for crypto             |
| `--with-nettle` / `--without-nettle`       | `HAVE_NETTLE`     | Use nettle crypto backend          |
| `--with-libgcrypt` / `--without-libgcrypt` | `HAVE_LIBGCRYPT`  | Use libgcrypt backend              |
| `--enable-acl` / `--disable-acl`           | `HAVE_ACL`        | Enable POSIX ACL support           |
| `--enable-xattr` / `--disable-xattr`       | `HAVE_XATTR`      | Enable extended attributes         |
| `--enable-iconv` / `--disable-iconv`       | `HAVE_ICONV`      | Enable character set conversion    |
| `--enable-xml2` / `--disable-xml2`         | `HAVE_LIBXML2`    | Enable libxml2 support (e.g., xar) |
| `--enable-expat` / `--disable-expat`       | `HAVE_LIBEXPAT`   | Enable expat XML support           |
