def run_camera(camera_config, camera_id, ws_loop):
    cap = get_video_source(camera_config)
    estimator = PoseEstimator()
    detector = SquatDetector()

    while True:
        frame = cap.read()
        pose = estimator.process(frame)
        feedback = detector.check(pose)

        if feedback:
            send_error_threadsafe({
                "clientId": camera_id,
                "feedback": feedback,
                "phase": detector.phase
            })