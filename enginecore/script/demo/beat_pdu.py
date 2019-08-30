#!/usr/bin/python3
"""This script attempts to extract beats from a music track;
Then it plays the track using ffplay & toggles PDU outlets on beats (which can
power light bulbs & flash them in sync with music).

Install:
    python3 -m pip install librosa numpy matplotlib

Usage:
    beat_pdu.py -H 10.42.1.94 localhost:1025 -t ~/Music/Imperial.mp3 

*Note* that redis listener runs at 0.5 delay so it would need to be changed to 0.01
   like: Timer(0.01, snmp_event, persist=True).register(self)
   (or change REDIS_LISTENER_SLEEP_TIME in redis_state_listener)

To model a virtual PDU for this script, create the following topology:

simengine-cli model drop

simengine-cli model create outlet -k1 -x=-70 -y=500
simengine-cli model create pdu -k4 --port=1025 -x=31 -y=700

simengine-cli model create lamp -k62 --power-consumption=120 -x=223 -y=595
simengine-cli model create lamp -k65 --power-consumption=120 -x=493 -y=595
simengine-cli model create lamp -k68 --power-consumption=120 -x=764 -y=594


simengine-cli model power-link -s1 -d4

simengine-cli model power-link -s42 -d62
simengine-cli model power-link -s45 -d65
simengine-cli model power-link -s48 -d68

"""
import subprocess
import time
import threading
from datetime import datetime as dt
import argparse

import librosa
import librosa.display

import numpy as np
import matplotlib.pyplot as plt

# toggle this to manage frequency of snmp requests
THRESHOLD_LOW = 0.25
THRESHOLD_INTENSE = 0.34


def _toggle_out_status(pdu_host, out_num, out_status):
    """Query snmp interface & set outlet status to on/off"""

    oid = "1.3.6.1.4.1.318.1.1.12.3.3.1.1.4." + str(out_num)
    command = "snmpset -v 1 -c private {host} {oid} i {status}".format(
        host=pdu_host, oid=oid, status=out_status
    )
    subprocess.Popen(command, shell=True)


def play_onset(hosts, times, norm_onset):
    """Toggle outlets when onset strength reaches specific level
    Args:
        hosts: snmp addresses of pdus
    """
    old_beat = 0
    status = 1
    old_beat_timestamp = dt.now()

    for idx, beat in enumerate(times):
        sleep_time = beat - old_beat if old_beat else beat
        time.sleep(sleep_time)
        new_beat_timestamp = dt.now()

        if (
            norm_onset[idx] > THRESHOLD_LOW
            and (new_beat_timestamp - old_beat_timestamp).microseconds / 1000 > 20
        ):
            print("BEAT [{}] -> STRENGTH [{}]".format(beat, norm_onset[idx]))
            if status == 1:
                status = 2
            else:
                status = 1

            old_beat_timestamp = new_beat_timestamp

            [_toggle_out_status(host, 5, status) for host in hosts]

            # toggle 2 extra outlets when things get very intense
            if norm_onset[idx] > THRESHOLD_INTENSE:
                for host in hosts:
                    _toggle_out_status(host, 8, status)
                    _toggle_out_status(host, 7, status)

        old_beat = beat


def play_beat(hosts, times, beats):
    old_beat = 0
    status = 1
    for beat in times[beats]:
        time.sleep(beat - old_beat if old_beat else beat)

        if status == 1:
            status = 2
        else:
            status = 1

        print("**BEAT")
        [_toggle_out_status(host, 2, status) for host in hosts]

        # _toggle_out_status("10.42.1.94", 2, status)
        old_beat = beat


def play_track(track):
    # Play track on this computer
    time.sleep(0.1)  # <- hard do sync pdu with ffplay, use this to manually adjust
    subprocess.Popen("ffplay " + track, shell=True)


def play_track_and_lights(track, hosts):
    """Extracts beats & strength envelope from a track &
    then launches 3 threads:
        1 playing music track
        1 toggling outlets on onset strengths
        1 toggling outlets on beat
    Args:
        track: path to mp3 file
        hosts(list): snmp hosts participating in disco
    """
    y, sr = librosa.load(track)

    # extract beat & track onset
    onset_env = librosa.onset.onset_strength(y, sr=sr, aggregate=np.median)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)

    times = librosa.frames_to_time(np.arange(len(onset_env)), sr=sr, hop_length=512)
    norm_onset = librosa.util.normalize(onset_env)

    track_t = threading.Thread(target=play_track, args=((track,)))
    onset_t = threading.Thread(target=play_onset, args=((hosts, times, norm_onset)))
    beat_t = threading.Thread(target=play_beat, args=((hosts, times, beats)))

    track_t.daemon = True
    onset_t.daemon = True
    beat_t.daemon = True

    track_t.start()
    onset_t.start()
    beat_t.start()

    track_t.join()
    onset_t.join()
    beat_t.join()


if __name__ == "__main__":

    argparser = argparse.ArgumentParser(
        description="Play a music track with PDUs accompaniment"
    )

    argparser.add_argument(
        "-H",
        "--hosts",
        help="Snmp Hosts to be used for disco lighting",
        nargs="+",
        type=str,
        required=True,
    )
    argparser.add_argument(
        "-t", "--track", help="Path to .mp3 music track", type=str, required=True
    )

    args = vars(argparser.parse_args())
    play_track_and_lights(args["track"], list(args["hosts"]))
