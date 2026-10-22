"""Closed hypothesis and action vocabulary for System-2."""
from enum import Enum
from itertools import combinations

class Primitive(str, Enum):
    SENSOR_BIAS = "SENSOR_BIAS"
    VELOCITY_OFFSET = "VELOCITY_OFFSET"
    SPEED_STEP = "SPEED_STEP"
    ACTUATOR_DELAY = "ACTUATOR_DELAY"

class FaultHypothesis(str, Enum):
    SENSOR_STUCK = "SENSOR_STUCK"
    SENSOR_SPIKE_OR_UNRELIABLE = "SENSOR_SPIKE_OR_UNRELIABLE"
    OBJECT_MISSING_OR_DROPPED = "OBJECT_MISSING_OR_DROPPED"
    BELT_STOP_OR_MOTION_LOSS = "BELT_STOP_OR_MOTION_LOSS"
    POST_VERIFICATION_CHANGE = "POST_VERIFICATION_CHANGE"
    UNKNOWN_OR_INSUFFICIENT_EVIDENCE = "UNKNOWN_OR_INSUFFICIENT_EVIDENCE"

class Action(str, Enum):
    UPDATE_MODEL_AND_REPLAN = "UPDATE_MODEL_AND_REPLAN"
    PAUSE_AND_REOBSERVE = "PAUSE_AND_REOBSERVE"
    HUMAN_ESCALATION = "HUMAN_ESCALATION"

def structures():
    p = tuple(Primitive)
    return tuple((x,) for x in p) + tuple(combinations(p, 2)) + tuple(combinations(p, 3))
