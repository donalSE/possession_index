from typing import List, Tuple

import norfair
import numpy as np
import pandas as pd
from norfair import Detection
from norfair.camera_motion import MotionEstimator

from inference import Converter
from inference.object_detector import ObjectDetection
from game import Ball, Match

def get_sahi_ball_detections(
    ball_detector, frame: np.ndarray
) -> List[norfair.Detection]:
    """
    Uses custom Yolov5 detector in order
    to get the predictions of the ball and converts it to
    Norfair.Detection list.

    Parameters
    ----------
    ball_detector : YoloV5
        YoloV5 detector for balls
    frame : np.ndarray
        Frame to get the ball detections from

    Returns
    -------
    List[norfair.Detection]
        List of ball detections
    """
    ball = ball_detector.predict(frame)
    detections = ball_detector.return_Detections(ball)

    # Filter out the detections based on class_id and confidence
    valid_detections = [
        detection for detection in detections
        if detection.class_id == 0 and detection.confidence > 0.05
    ]

    return Converter.sahi_DataFrame_to_Detections(valid_detections)

def get_ball_detections(
    ball_detector, frame: np.ndarray
) -> List[norfair.Detection]:
    """
    Uses custom Yolov5 detector in order
    to get the predictions of the ball and converts it to
    Norfair.Detection list.

    Parameters
    ----------
    ball_detector : YoloV5
        YoloV5 detector for balls
    frame : np.ndarray
        Frame to get the ball detections from

    Returns
    -------
    List[norfair.Detection]
        List of ball detections
    """
    ball = ball_detector.predict(frame)
    ball = ball_detector.return_Detections(ball)
    ball = ball[ball.class_id == 0]
    ball = ball[ball.confidence > 0.05]
    return Converter.DataFrame_to_Detections(ball)


def get_person_detections(
    person_detector, frame: np.ndarray
) -> Tuple[List[norfair.Detection], List[norfair.Detection]]:
    """
    Uses YoloV5 Detector in order to detect the players
    in a match and filter out the detections that are not players
    and have confidence lower than 0.35.

    Parameters
    ----------
    person_detector : YoloV5
        YoloV5 detector
    frame : np.ndarray
        _description_

    Returns
    -------
    List[norfair.Detection]
        List of player detections
    """

    persons = person_detector.predict(frame)
    persons = person_detector.return_Detections(persons)
    persons = persons[persons.confidence > 0.7]
    players = persons[persons.class_id == 2]
    referee = persons[persons.class_id == 3]
    player_detections = Converter.DataFrame_to_Detections(players)
    referee_detections = Converter.DataFrame_to_Detections(referee)
    return player_detections, referee_detections

def get_sahi_person_detections(
    person_detector, frame: np.ndarray
) -> Tuple[List[norfair.Detection], List[norfair.Detection]]:
    """
    Uses YoloV5 Detector in order to detect the players
    in a match and filter out the detections that are not players
    and have confidence lower than 0.35.

    Parameters
    ----------
    person_detector : YoloV5
        YoloV5 detector
    frame : np.ndarray
        _description_

    Returns
    -------
    List[norfair.Detection]
        List of player detections
    """

    detections = person_detector.predict(frame)
    detections = person_detector.return_Detections(detections)
    # Filter out the detections based on class_id and confidence
    person_detections = [
        detection for detection in detections
        if detection.class_id == 2 and detection.confidence > 0.07
    ]

    return Converter.sahi_DataFrame_to_Detections(person_detections)

def create_mask(frame: np.ndarray, detections: List[norfair.Detection]) -> np.ndarray:
    """

    Creates mask in order to hide detections and goal counter for motion estimation

    Parameters
    ----------
    frame : np.ndarray
        Frame to create mask for.
    detections : List[norfair.Detection]
        Detections to hide.

    Returns
    -------
    np.ndarray
        Mask.
    """

    if not detections:
        mask = np.ones(frame.shape[:2], dtype=frame.dtype)
    else:
        detections_df = Converter.Detections_to_DataFrame(detections)
        mask = ObjectDetection.generate_predictions_mask(detections_df, frame, margin=40)

    # remove goal counter
    mask[69:200, 160:510] = 0

    return mask


def apply_mask(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Applies a mask to an img

    Parameters
    ----------
    img : np.ndarray
        Image to apply the mask to
    mask : np.ndarray
        Mask to apply

    Returns
    -------
    np.ndarray
        img with mask applied
    """
    masked_img = img.copy()
    masked_img[mask == 0] = 0
    return masked_img


def update_motion_estimator(
    motion_estimator: MotionEstimator,
    detections: List[Detection],
    frame: np.ndarray,
) -> "CoordinatesTransformation":
    """

    Update coordinate transformations every frame

    Parameters
    ----------
    motion_estimator : MotionEstimator
        Norfair motion estimator class
    detections : List[Detection]
        List of detections to hide in the mask
    frame : np.ndarray
        Current frame

    Returns
    -------
    CoordinatesTransformation
        Coordinate transformation for the current frame
    """

    mask = create_mask(frame=frame, detections=detections)
    coord_transformations = motion_estimator.update(frame, mask=mask) # should have mask=mask in args
    return coord_transformations


def get_main_ball(detections: List[Detection], match: Match = None) -> Ball:
    """
    Gets the main ball from a list of balls detection

    The match is used in order to set the color of the ball to
    the color of the team in possession of the ball.

    Parameters
    ----------
    detections : List[Detection]
        List of detections
    match : Match, optional
        Match object, by default None

    Returns
    -------
    Ball
        Main ball
    """
    ball = Ball(detection=None)

    if match:
        ball.set_color(match)

    if detections:
        ball.detection = detections[0]

    return ball

