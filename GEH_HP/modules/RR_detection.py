import json
import pyedflib
import numpy as np
# install from https://pypi.org/project/py-ecg-detectors/
from ecgdetectors import Detectors
# Unable to install
# from signal_utils import Signal
# UNUSED
from wfdb import processing
# lussubg
# import  .signals.ecg as bsp_ecg
# import biosppy.signals.tools as bsp_tools
# UNUSED
import pandas as pd


MATCHING_QRS_FRAMES_TOLERANCE = 50 # We consider two matching QRS as QRS frames within a 50 milliseconds window
MAX_SINGLE_BEAT_DURATION = 1800 # We consider the laximum duration of a beat in milliseconds - 33bpm


ecg_data = np.array(0)
data = {}
fs = 180

# List of RR detection algorithms

def detect_qrs_swt(ecg_data, fs):
    qrs_frames = []
    try:
        detectors = Detectors(fs) # Explain why
        qrs_frames = detectors.swt_detector(ecg_data)
    except Exception:
        # raise ValueError("swt")
        print("Exception in detect_qrs_swt")
    return qrs_frames


def detect_qrs_xqrs(ecg_data, fs):
    qrs_frames = []
    try:
        qrs_frames = processing.xqrs_detect(sig=ecg_data, fs=fs, verbose=False)
    except Exception:
        print("Exception in detect_qrs_xqrs")
    # return qrs_frames.tolist()
    return qrs_frames


def detect_qrs_gqrs(ecg_data, fs):
    qrs_frames = []
    try:
        qrs_frames = processing.qrs.gqrs_detect(sig=ecg_data, fs=fs)
    except Exception:
        print("Exception in detect_qrs_gqrs")
    return qrs_frames.tolist()


# Centralising function

def get_cardiac_infos(ecg_data, fs, method):
    if method == "xqrs":
        qrs_frames = detect_qrs_xqrs(ecg_data, fs) # Explain
    elif method == "gqrs":
        qrs_frames = detect_qrs_gqrs(ecg_data, fs*2) # Explain
    elif method == "swt":
        qrs_frames = detect_qrs_gqrs(ecg_data, fs*2) # Explains

    rr_intervals = np.zeros(0)
    hr = np.zeros(0)
    if len(qrs_frames):
        rr_intervals = to_rr_intervals(qrs_frames, fs)
        hr = to_hr(rr_intervals)
    return qrs_frames, rr_intervals, hr


# UTILITIES

def to_rr_intervals(frame_data, fs):
    rr_intervals = np.zeros(len(frame_data) - 1)
    for i in range(0, (len(frame_data) - 1)):
        rr_intervals[i] = (frame_data[i+1] - frame_data[i]) * 1000.0 / fs

    return rr_intervals

def to_hr(rr_intervals):
    hr = np.zeros(len(rr_intervals))
    for i in range(0, len(rr_intervals)):
        hr[i] = (int)(60 * 1000 / rr_intervals[i])

    return hr

def compute_qrs_frames_correlation(fs, qrs_frames_1, qrs_frames_2):
    single_frame_duration = 1./fs

    frame_tolerance = MATCHING_QRS_FRAMES_TOLERANCE * (
        0.001 / single_frame_duration)
    max_single_beat_frame_duration = MAX_SINGLE_BEAT_DURATION  * (
        0.001 / single_frame_duration)

    #Catch complete failed QRS detection
    if (len(qrs_frames_1) == 0 or len(qrs_frames_2) == 0):
        return 0, 0, 0

    i = 0
    j = 0
    matching_frames = 0

    previous_min_qrs_frame = min(qrs_frames_1[0], qrs_frames_2[0])
    missing_beats_frames_count = 0

    while i < len(qrs_frames_1) and j < len(qrs_frames_2):
        min_qrs_frame = min(qrs_frames_1[i], qrs_frames_2[j])
        # Get missing detected beats intervals
        if (min_qrs_frame - previous_min_qrs_frame) > (
            max_single_beat_frame_duration):
            missing_beats_frames_count += (min_qrs_frame -
                previous_min_qrs_frame)

        # Matching frames

        if abs(qrs_frames_2[j] - qrs_frames_1[i]) < frame_tolerance:
            matching_frames += 1
            i += 1
            j += 1
        else:
            # increment first QRS in frame list
            if min_qrs_frame == qrs_frames_1[i]:
                i += 1
            else:
                j += 1
        previous_min_qrs_frame = min_qrs_frame

    correlation_coefs = 2 * matching_frames / (len(qrs_frames_1) +
        len(qrs_frames_2))

    missing_beats_duration = missing_beats_frames_count * single_frame_duration
    correlation_coefs = round(correlation_coefs, 2)
    return correlation_coefs, matching_frames, missing_beats_duration


def make_report(data):
    # Start of the report

    # Number of frames

    print(
        "\nTotal detected QRS frames GQRS " +
        str(len(data['gqrs']['qrs'])) +
        " XQRS " +
        str(len(data['xqrs']['qrs'])) +
        " Swt " +
        str(len(data['swt']['qrs']))
        )


    # HR

    print(
        "\nAverage Heart rate " +
        str(np.average(data['gqrs']['hr'])) +
        " XQRS " +
        str(np.average(data['xqrs']['hr'])) +
        " Swt " +
        str(np.average(data['swt']['hr']))
        )


    # Coef score

    print(
        "\nCorrelation coef gqrs" +
        str(data['score']['corrcoefs']['gqrs']) +
        "\nCorrelation coef XQRS" +
        str(data['score']['corrcoefs']['xqrs']) +
        "\nCorrelation coef Swt" +
        str(data['score']['corrcoefs']['swt'])
        )

    # Matching frames

    print(
        "\nMatching frames gqrs" +
        str(data['score']['matching_frames']['gqrs']) +
        "\nMatching frames XQRS" +
        str(data['score']['matching_frames']['xqrs']) +
        "\nMatching frames Swt" +
        str(data['score']['matching_frames']['swt'])
        )

    # Missing beats duration

    print(
        "\nMissing beats duration gqrs" +
        str(data['score']['matching_frames']['gqrs']) +
        "\nMissing beats duration XQRS" +
        str(data['score']['matching_frames']['xqrs']) +
        "\nMissing beats duration Swt" +
        str(data['score']['matching_frames']['swt'])
        )

class compute_heart_rate:

    def __init__(self, fs=128):
        self.fs = fs
        self.data = {"infos": {"sampling_freq": None
                         },
                     "gqrs": {"qrs": None,
                                 "rr_intervals": None,
                                 "hr": None
                                 },
                     "xqrs": {"qrs": None,
                                 "rr_intervals": None,
                                 "hr": None
                                 },
                     "swt": {"qrs": None,
                             "rr_intervals": None,
                             "hr": None
                             },
                     "score": {"corrcoefs":
                         {"gqrs": None,
                         "xqrs": None,
                         "swt": None
                         },
                             "matching_frames":
                         {"gqrs": None,
                         "xqrs": None,
                         "swt": None
                         },
                             "missing_beats_duration":
                         {"gqrs": None,
                         "xqrs": None,
                         "swt": None
                         }
                         }
                     }

    def compute(self, df_input):

            ecg_data = np.array(df_input['ECG'].values)

            qrs_frames_gqrs, rr_intervals_gqrs, hr_gqrs = get_cardiac_infos(
                ecg_data, fs, "gqrs")
            qrs_frames_xqrs, rr_intervals_xqrs, hr_xqrs = get_cardiac_infos(
                ecg_data, fs, "xqrs")
            qrs_frames_swt, rr_intervals_swt, hr_swt = get_cardiac_infos(
                ecg_data, fs, "swt")

            frame_correl_1, matching_frames_1, missing_beats_duration_1 = \
                compute_qrs_frames_correlation(fs, qrs_frames_gqrs, qrs_frames_xqrs)
            frame_correl_2, matching_frames_2, missing_beats_duration_2 = \
                compute_qrs_frames_correlation(fs, qrs_frames_gqrs, qrs_frames_swt)
            frame_correl_3, matching_frames_3, missing_beats_duration_3 = \
                compute_qrs_frames_correlation(fs, qrs_frames_xqrs, qrs_frames_swt)

            self.data = {"infos": {"sampling_freq":fs
                                },
                        "gqrs": {"qrs": qrs_frames_gqrs,
                                "rr_intervals": rr_intervals_gqrs.tolist(),
                                "hr": hr_gqrs.tolist()
                                },
                        "xqrs": {"qrs": qrs_frames_xqrs,
                                "rr_intervals": rr_intervals_xqrs.tolist(),
                                "hr": hr_xqrs.tolist()
                                },
                        "swt": {"qrs": qrs_frames_swt,
                                "rr_intervals":rr_intervals_swt.tolist(),
                                "hr": hr_swt.tolist()
                                },
                        "score": {"corrcoefs":
                            {"gqrs": [1, frame_correl_1, frame_correl_2],
                            "xqrs": [frame_correl_1, 1, frame_correl_3],
                            "swt": [frame_correl_2, frame_correl_3, 1]
                            },
                                "matching_frames":
                            {"gqrs": [1, matching_frames_1, matching_frames_2],
                            "xqrs": [matching_frames_1, 1, matching_frames_3],
                            "swt": [matching_frames_2, matching_frames_3, 1]
                            },
                                "missing_beats_duration":
                            {"gqrs": [1, missing_beats_duration_1, missing_beats_duration_2],
                            "xqrs": [missing_beats_duration_1, 1, missing_beats_duration_3],
                            "swt": [missing_beats_duration_2, missing_beats_duration_3, 1]
                            }
                            }
                        }


# TO DO: make a variable

if __name__ == "__main__":

    df_input = pd.read_csv('data/simulation/df_simulation-timestamp.csv',
        sep=';')
    # fs = 128

    compute_hr = compute_heart_rate()
    compute_hr.compute(df_input=df_input)
    data = compute_hr.data
    make_report(data)


    # temp_df = pd.DataFrame(columns=['RR'])
    # temp_df['RR'] = data['gqrs']['hr']
    # temp_df.to_csv('data/record/export_rr.csv')
    # print('\nExport ok')