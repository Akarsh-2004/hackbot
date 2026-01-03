import re
import json
import xml.etree.ElementTree as ET

class ToolParser:
    """Base class for tool output parsers"""
    
    @staticmethod
    def detect(text):
        """Detect if text is from this tool"""
        raise NotImplementedError
    
    @staticmethod
    def parse(text):
        """Parse tool output into structured data"""
        raise NotImplementedError

class NmapParser(ToolParser):
    @staticmethod
    def detect(text):
        return "Nmap scan report" in text or "<?xml" in text and "nmaprun" in text
    
    @staticmethod
    def parse(text):
        """Parse nmap output (text or XML)"""
        result = {
            "tool": "nmap",
            "hosts": [],
            "summary": {}
        }
        
        # Try XML first
        if "<?xml" in text and "nmaprun" in text:
            try:
                root = ET.fromstring(text)
                for host in root.findall(".//host"):
                    addr = host.find(".//address[@addrtype='ipv4']")
                    if addr is not None:
                        host_data = {
                            "ip": addr.get("addr"),
                            "ports": []
                        }
                        
                        for port in host.findall(".//port"):
                            state = port.find("state")
                            service = port.find("service")
                            host_data["ports"].append({
                                "port": port.get("portid"),
                                "protocol": port.get("protocol"),
                                "state": state.get("state") if state is not None else "unknown",
                                "service": service.get("name") if service is not None else "unknown"
                            })
                        
                        result["hosts"].append(host_data)
                return result
            except:
                pass
        
        # Fallback to text parsing
        lines = text.split("\n")
        current_host = None
        
        for line in lines:
            # Detect host
            if "Nmap scan report for" in line:
                ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", line)
                if ip_match:
                    current_host = {"ip": ip_match.group(), "ports": []}
                    result["hosts"].append(current_host)
            
            # Detect open ports
            elif current_host and re.match(r"^\d+/", line):
                parts = line.split()
                if len(parts) >= 3:
                    port_proto = parts[0].split("/")
                    current_host["ports"].append({
                        "port": port_proto[0],
                        "protocol": port_proto[1] if len(port_proto) > 1 else "tcp",
                        "state": parts[1],
                        "service": parts[2] if len(parts) > 2 else "unknown"
                    })
        
        # Generate summary
        all_ports = []
        for host in result["hosts"]:
            all_ports.extend([p["port"] for p in host["ports"] if p["state"] == "open"])
        
        result["summary"] = {
            "total_hosts": len(result["hosts"]),
            "open_ports": list(set(all_ports))
        }
        
        return result

class NiktoParser(ToolParser):
    @staticmethod
    def detect(text):
        return "Nikto" in text or "- Nikto v" in text
    
    @staticmethod
    def parse(text):
        """Parse nikto output"""
        result = {
            "tool": "nikto",
            "target": None,
            "findings": []
        }
        
        lines = text.split("\n")
        
        for line in lines:
            # Extract target
            if "+ Target IP:" in line or "+ Target Host:" in line:
                result["target"] = line.split(":")[-1].strip()
            
            # Extract findings (lines starting with +)
            if line.strip().startswith("+") and "OSVDB" in line or "CVE" in line:
                result["findings"].append(line.strip())
        
        result["summary"] = {
            "total_findings": len(result["findings"])
        }
        
        return result

def auto_parse(text):
    """Automatically detect and parse tool output"""
    parsers = [NmapParser, NiktoParser]
    
    for parser in parsers:
        if parser.detect(text):
            return parser.parse(text)
    
    return None

if __name__ == "__main__":
    # Test nmap parser
    nmap_sample = """
    Nmap scan report for 10.10.10.1
    PORT     STATE SERVICE
    22/tcp   open  ssh
    80/tcp   open  http
    445/tcp  open  microsoft-ds
    """
    
    parsed = auto_parse(nmap_sample)
    print(json.dumps(parsed, indent=2))
