from __future__ import annotations

import abc
import operator
import types


class FileReader:
    @classmethod
    def get_reader(cls, name: str, encoding: str) -> FileReader:
        for subcls in cls.__subclasses__():
            if subcls is TextFileReader:
                continue
            if subcls._can_read(name):
                return subcls(name, encoding)
        return TextFileReader(name, encoding)

    @classmethod
    @abc.abstractmethod
    def _can_read(cls, fname: str) -> bool:
        """Override in subclasses"""

    @abc.abstractmethod
    def _close_reader(self):
        """Override in subclasses"""

    def __init__(self, file_name: str, encoding: str):
        self.file_name = file_name
        self.encoding = encoding
        self._iter = iter(())

    def __iter__(self):
        return self._iter

    def __next__(self):
        try:
            return next(self._iter)
        except StopIteration:
            self._close_reader()
            raise


class TextFileReader(FileReader):
    @classmethod
    def _can_read(cls, fname: str) -> bool:
        return True

    def __init__(self, fname: str, encoding: str):
        super().__init__(fname, encoding)
        self._close_obj = open(self.file_name, encoding=self.encoding)
        self._iter = self._close_obj

    def _close_reader(self):
        self._close_obj.close()


class InternalDemoReader(FileReader):
    @classmethod
    def _can_read(cls, fname: str) -> bool:
        return fname.endswith(".demo")

    def __init__(self, fname: str, encoding: str):
        import logmerger.demo as demo_files

        super().__init__(fname, encoding)
        self._close_obj = None
        var_name = fname.partition(".")[0]
        body = getattr(demo_files, var_name)
        self._iter = iter(body.splitlines())

    def _close_reader(self):
        pass


class GzipFileReader(FileReader):
    @classmethod
    def _can_read(cls, fname: str) -> bool:
        return fname.endswith(".gz")

    def __init__(self, fname: str, encoding: str):
        import gzip

        super().__init__(fname, encoding)
        self._close_obj = gzip.GzipFile(filename=self.file_name)
        self._iter = (s.decode(self.encoding) for s in self._close_obj)
        # make fake stat result
        self.file_stat = types.SimpleNamespace(st_ctime=self._close_obj.mtime)

    def _close_reader(self):
        self._close_obj.close()


class PcapFileReader(FileReader):
    nfs_procedure_map = {
        "0": "NULL",
        "1": "GETATTR",  # : get file attributes
        "2": "SETATTR",  # : set file attributes
        "3": "LOOKUP",  # : look up file name
        "4": "ACCESS",
        "5": "READLINK",  # : read from symbolic link
        "6": "READ",  # : read from file
        "7": "WRITE",  # : write to file
        "8": "CREATE",  # : create file
        "9": "MKDIR",  # : create directory
        "10": "SYMLINK",  # : create link to file
        "11": "MKNOD",
        "12": "REMOVE",  # : remove file
        "13": "RMDIR",  # : remove directory
        "14": "RENAME",  # : rename file
        "15": "LINK",  # : create symbolic link
        "16": "READDIR",  # : read from directory
        "17": "READDIR+",  # : read from directory
        "18": "FSSTAT",  # : get filesystem attributes
        "19": "FSINFO",  # : get filesystem attributes
        "20": "PATHCONF",
        "21": "COMMIT",
    }

    tcp_flags = [
        (1, 'FIN'),
        (2, 'SYN'),
        (4, 'RST'),
        (8, 'PSH'),
        (16, 'ACK'),
        (32, 'URG'),
    ]

    @classmethod
    def _can_read(cls, fname: str) -> bool:
        return fname.endswith(".pcap")

    def __init__(self, fname: str, encoding: str):
        try:
            import pyshark
        except ImportError:
            print("cannot merge PCAP contents; install PCAP support using `pip install logmerger[pcap]`")
            exit(1)

        super().__init__(fname, encoding)
        self._close_obj = pyshark.FileCapture(fname, keep_packets=False)
        self._iter = (self.format_packet(pkt) for pkt in self._close_obj if "IP" in pkt)

    def _close_reader(self) -> None:
        self._close_obj.close()

    def format_packet(self, pkt, extractor=operator.itemgetter("timestamp", "message")) -> str:
        pkt_dict = self.extract_packet(pkt)
        return " ".join(extractor(pkt_dict))  # f"{pkt_dict['timestamp']} {pkt_dict['message']}"

    def extract_packet(self, pkt) -> dict[str, str]:
        import errno

        timestamp = pkt.sniff_time
        ip_info = pkt.ip
        content = ""

        if 'TCP' in pkt:
            tcp_info = pkt.tcp
            from_, dir_, to_ = ((ip_info.src, tcp_info.srcport), "->", (ip_info.dst, tcp_info.dstport))

            if 'NFS' in pkt:
                nfs_info = pkt.nfs
                pkt_proc = self.nfs_procedure_map.get(nfs_info.procedure_v3, '???')
                pkt_fname = getattr(nfs_info, 'name', '')
                status_str = ""
                if hasattr(nfs_info, 'status'):
                    from_, dir_, to_ = to_, "<-", from_
                    if nfs_info.status != "0":
                        status_str = errno.errorcode.get(int(nfs_info.status), f"UNKERR:{nfs_info.status}")
                    else:
                        status_str = "OK"

                content = f"{pkt_proc} {pkt_fname!r} {status_str}" if pkt_fname else f"{pkt_proc} {status_str}"
                return {
                    "timestamp": str(timestamp)[:23],
                    "proto": f"{pkt.highest_layer}",
                    "message": f"{pkt.highest_layer} {from_[0]}:{from_[1]} {dir_} {to_[0]}:{to_[1]} seq:{tcp_info.seq} ack:{tcp_info.ack} {content}",
                }

            elif "HTTP" in pkt:
                http_info = pkt.http
                eol_string = r"\r\n"
                content = http_info.chat.removesuffix(eol_string).rstrip()
                proto = f"HTTP{('/' + pkt.highest_layer) if pkt.highest_layer != 'HTTP' else ''}"

                return {
                    "timestamp": str(timestamp)[:23],
                    "proto":  "HTTP",
                    "message": f"{proto} {from_[0]}:{from_[1]} {dir_} {to_[0]}:{to_[1]} seq:{tcp_info.seq} ack:{tcp_info.ack} {content!r}",
                }

            else:
                # just report TCP basic information
                tcp_flags_int = int(tcp_info.flags[3:], 16)
                flg_str = ','.join(flg for iflg, flg in self.tcp_flags if tcp_flags_int & iflg)
                if hasattr(tcp_info, "payload"):
                    payload = f"{tcp_info.payload:.48s}{'...' if int(tcp_info.len) > 16 else ''}"
                    content = f"{flg_str} {payload}"
                else:
                    content = flg_str

                return {
                    "timestamp": str(timestamp)[:23],
                    "proto": f"{pkt.highest_layer}",
                    "message": f"{pkt.highest_layer} {from_[0]}:{from_[1]} {dir_} {to_[0]}:{to_[1]} seq:{tcp_info.seq} ack:{tcp_info.ack} {content}",
                }
        else:
            # not TCP, just report basic packet source/dest information
            return {
                "timestamp": str(timestamp)[:23],
                "proto": f"{pkt.highest_layer}",
                "message": f"{pkt.highest_layer} {ip_info.src} -> {ip_info.dst} {content}",
            }
