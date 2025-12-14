import os
import time
from kirosu.utils import TaskSplitter

def main():
    # Configuration
    HOST = "127.0.0.1"
    PORT = int(os.environ.get("KIRO_SWARM_PORT", 8765))
    
    splitter = TaskSplitter(HOST, PORT)
    
    # 1. Generate Dummy Data (100 documents)
    documents = [f"Document {i}: This is some content for document number {i}." for i in range(100)]
    print(f"Generated {len(documents)} documents.")
    
    # 2. Split and Enqueue
    print("Enqueuing tasks...")
    task_ids = splitter.split_and_enqueue(
        items=documents,
        prompt_template="Summarize this text: {item}",
        batch_size=5, # Process 5 docs per task
        task_type="chat"
    )
    print(f"Enqueued {len(task_ids)} tasks.")
    
    # 3. Wait for Completion
    print("Waiting for swarm to finish...")
    results = splitter.wait_for_completion(task_ids)
    
    # 4. Aggregate
    print("\nResults:")
    for tid, task in results.items():
        status = "✅" if task["status"] == "done" else "❌"
        print(f"Task {tid} [{status}]: {task.get('result', '')[:50]}...")

if __name__ == "__main__":
    main()
