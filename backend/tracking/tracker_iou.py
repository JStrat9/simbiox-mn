# tracking/tracker_iou.py

import numpy as np 

class CentroidTracker:
    def __init__(self, max_clients=6, distance_threshold=100):
        self.max_clients = max_clients
        self.distance_threshold = distance_threshold
        self.client_centroids = {} # client_id -> last centroid
        self.available_ids = [str(i + 1) for i in range(max_clients)]
    
    def get_client_id(self, centroid):
        min_dist = float('inf')
        matched_id = None

        for cid, last_centroid in self.client_centroids.items():
            dist = np.linalg.norm(np.array(centroid) - np.array(last_centroid))
            if dist < min_dist and dist < self.distance_threshold:
                min_dist = dist
                matched_id = cid

        if matched_id is None:
            if not self.available_ids:
                raise RuntimeError("No available IDs for new person")
            matched_id = self.available_ids.pop(0)
            
        self.client_centroids[matched_id] = centroid
        return matched_id
    
    def release_missing(self, current_ids):
        lost_ids = set(self.client_centroids.keys()) - current_ids
        for lost_id in lost_ids:
            del self.client_centroids[lost_id]
            self.available_ids.append(lost_id)