import json
import os
from datetime import datetime

class Evaluator:
    """Tracks queries, responses, and user feedback for evaluation"""
    
    def __init__(self, log_dir="data/evaluation"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, "query_log.jsonl")
        self.metrics_file = os.path.join(log_dir, "metrics.json")
        self.metrics = self._load_metrics()
    
    def _load_metrics(self):
        if os.path.exists(self.metrics_file):
            with open(self.metrics_file, "r") as f:
                return json.load(f)
        return {
            "total_queries": 0,
            "avg_response_time": 0,
            "thumbs_up": 0,
            "thumbs_down": 0,
            "confidence_distribution": {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        }
    
    def log_query(self, query, response, confidence, response_time, feedback=None):
        """Log a query and its response"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "confidence": confidence,
            "response_time": response_time,
            "feedback": feedback
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Update metrics
        self.metrics["total_queries"] += 1
        self.metrics["confidence_distribution"][confidence] += 1
        
        # Update average response time
        n = self.metrics["total_queries"]
        old_avg = self.metrics["avg_response_time"]
        self.metrics["avg_response_time"] = (old_avg * (n - 1) + response_time) / n
        
        if feedback == "up":
            self.metrics["thumbs_up"] += 1
        elif feedback == "down":
            self.metrics["thumbs_down"] += 1
        
        self._save_metrics()
    
    def _save_metrics(self):
        with open(self.metrics_file, "w") as f:
            json.dump(self.metrics, f, indent=2)
    
    def get_report(self):
        """Generate evaluation report"""
        total = self.metrics["total_queries"]
        if total == 0:
            return "No queries logged yet."
        
        satisfaction = (self.metrics["thumbs_up"] / 
                       (self.metrics["thumbs_up"] + self.metrics["thumbs_down"]) * 100
                       if (self.metrics["thumbs_up"] + self.metrics["thumbs_down"]) > 0 else 0)
        
        report = f"""
Evaluation Report
=================
Total Queries: {total}
Avg Response Time: {self.metrics['avg_response_time']:.2f}s
User Satisfaction: {satisfaction:.1f}%
  👍 {self.metrics['thumbs_up']}
  👎 {self.metrics['thumbs_down']}

Confidence Distribution:
  HIGH: {self.metrics['confidence_distribution']['HIGH']}
  MEDIUM: {self.metrics['confidence_distribution']['MEDIUM']}
  LOW: {self.metrics['confidence_distribution']['LOW']}
"""
        return report.strip()

if __name__ == "__main__":
    # Test
    evaluator = Evaluator()
    evaluator.log_query("test query", "test response", "HIGH", 2.5, "up")
    print(evaluator.get_report())
