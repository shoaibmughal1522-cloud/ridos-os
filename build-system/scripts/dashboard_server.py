#!/usr/bin/env python3
"""RIDOS Dashboard Stats Server - runs on port 9999"""
import json, os, socket, time
from http.server import HTTPServer, BaseHTTPRequestHandler
import psutil

class StatsHandler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass  # Suppress logs

    def do_GET(self):
        if self.path == '/stats':
            try:
                cpu = psutil.cpu_percent(interval=0.5)
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                net = psutil.net_if_addrs()
                uptime_s = time.time() - psutil.boot_time()
                uptime_h = int(uptime_s // 3600)
                uptime_m = int((uptime_s % 3600) // 60)

                # Get primary IP
                ip = 'N/A'
                iface = 'N/A'
                for name, addrs in net.items():
                    if name != 'lo':
                        for addr in addrs:
                            if addr.family == socket.AF_INET:
                                ip = addr.address
                                iface = name
                                break

                # Check internet
                inet = False
                try:
                    socket.setdefaulttimeout(2)
                    socket.socket().connect(("8.8.8.8", 53))
                    inet = True
                except: pass

                # Check API key
                ai_ready = os.path.exists('/etc/ridos/api.key') and \
                           os.path.getsize('/etc/ridos/api.key') > 10

                data = {
                    'cpu': round(cpu, 1),
                    'cpu_cores': psutil.cpu_count(),
                    'ram_percent': round(mem.percent, 1),
                    'ram_used': round(mem.used/1024**3, 1),
                    'ram_total': round(mem.total/1024**3, 1),
                    'disk_percent': round(disk.percent, 1),
                    'disk_used': round(disk.used/1024**3, 1),
                    'disk_total': round(disk.total/1024**3, 1),
                    'net_ip': ip,
                    'net_iface': iface,
                    'uptime': f"{uptime_h}h {uptime_m}m",
                    'internet': inet,
                    'ai_ready': ai_ready,
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 9999), StatsHandler)
    print("RIDOS Dashboard Stats Server running on port 9999")
    server.serve_forever()
