import json
import os
from datetime import datetime

class Session:
    """Manages target context and session state"""
    
    def __init__(self, session_name="default"):
        self.session_name = session_name
        self.targets = {}  # {target_id: target_data}
        self.current_target = None
        self.history = []
        self.session_dir = "data/sessions"
        os.makedirs(self.session_dir, exist_ok=True)
    
    def add_target(self, target_id, **kwargs):
        """Add or update a target"""
        if target_id not in self.targets:
            self.targets[target_id] = {
                "id": target_id,
                "created": datetime.now().isoformat(),
                "os": kwargs.get("os", "unknown"),
                "ports": kwargs.get("ports", []),
                "credentials": kwargs.get("credentials", []),
                "failed_attempts": kwargs.get("failed_attempts", []),
                "notes": kwargs.get("notes", []),
                "timeline": []
            }
        else:
            # Update existing target
            for key, value in kwargs.items():
                if key in ["ports", "credentials", "failed_attempts", "notes"]:
                    # Append to lists
                    if isinstance(value, list):
                        self.targets[target_id][key].extend(value)
                    else:
                        self.targets[target_id][key].append(value)
                else:
                    self.targets[target_id][key] = value
        
        self.current_target = target_id
        return self.targets[target_id]
    
    def log_action(self, action, result=None):
        """Log an action to the current target's timeline"""
        if self.current_target:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "result": result
            }
            self.targets[self.current_target]["timeline"].append(entry)
            self.history.append(entry)
    
    def get_target(self, target_id=None):
        """Get target data"""
        tid = target_id or self.current_target
        return self.targets.get(tid)
    
    def get_context_summary(self):
        """Get a formatted summary of the current target"""
        if not self.current_target:
            return "No active target."
        
        target = self.targets[self.current_target]
        summary = f"""
**Current Target**: {target['id']}
**OS**: {target.get('os', 'unknown')}
**Open Ports**: {', '.join(map(str, target.get('ports', []))) or 'None discovered'}
**Credentials Found**: {len(target.get('credentials', []))}
**Failed Attempts**: {len(target.get('failed_attempts', []))}
**Recent Actions**: {len(target.get('timeline', []))}
"""
        return summary.strip()
    
    def save(self, filename=None):
        """Save session to JSON"""
        filename = filename or f"{self.session_name}.json"
        filepath = os.path.join(self.session_dir, filename)
        
        data = {
            "session_name": self.session_name,
            "targets": self.targets,
            "current_target": self.current_target,
            "history": self.history
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        return filepath
    
    def load(self, filename=None):
        """Load session from JSON"""
        filename = filename or f"{self.session_name}.json"
        filepath = os.path.join(self.session_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Session file not found: {filepath}")
        
        with open(filepath, "r") as f:
            data = json.load(f)
        
        self.session_name = data.get("session_name", self.session_name)
        self.targets = data.get("targets", {})
        self.current_target = data.get("current_target")
        self.history = data.get("history", [])
        
        return self

if __name__ == "__main__":
    # Test
    session = Session("test_session")
    session.add_target("10.10.10.1", os="Linux", ports=[22, 80, 445])
    session.log_action("nmap scan", "3 ports open")
    session.add_target("10.10.10.1", credentials=["admin:password123"])
    
    print(session.get_context_summary())
    
    # Save and load
    filepath = session.save()
    print(f"\nSaved to: {filepath}")
    
    new_session = Session("test_session")
    new_session.load()
    print("\nLoaded session:")
    print(new_session.get_context_summary())
