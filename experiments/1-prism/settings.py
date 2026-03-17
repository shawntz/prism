'''global settings
'''
EXPERIMENT_NAME = "ecl"
STIM_DIRECTORY = "stimuli"
DATA_DIRECTORY = "data"

'''demo settings
'''
DEMO_RATE = 1 # note: change to a fraction to run the experiment in that fraction of time

'''trial timings
'''
ENC_PREGOAL_ITI = 4
ENC_GOAL = 1.6
ENC_PREPROBE_ITI = 0.1
ENC_PROBE = 2.8

RET_PREPROBE_ITI = 4
RET_PROBE = 5

REORIENTING_PROBE_TIME = 0.4
REORIENTING_PROBE_ERROR = 0.01
REORIENTING_FLICKER_RATE = 0.2
TRIGGER_WINDOW_MAX_TIME = 1
POST_TRIGGER_FIX_WINDOW_TIME = 1 ## 1 second total
POST_TRIGGER_P1_EPOCH_TIME = 1 ## 1000 ms
SD_TRIGGER_SCALE = 1
CTRL_PROBE_CONTIG_LIMIT = 3
MISSING_DATA_TOLERANCE = 0.2

'''goal strings
'''
ENC_CONCEPTUAL_GOAL = "Pleasant/Unpleasant?"
ENC_PERCEPTUAL_GOAL = "Bigger/Smaller?"

RET_CONCEPTUAL_GOAL = "Pleasant/Unpleasant Before?"
RET_PERCEPTUAL_GOAL = "Bigger/Smaller Before?"
RET_NOVEL_GOAL = "New Item?"

'''response key mappings
notes: create & enable profile for ps5 dualsense controller using the 'Enjoyable' app (https://yukkurigames.com/enjoyable/), 
and then normal event.waitkeys function from psychopy will recognize controller input as keyboard input
'''
RESPONSE_KEY_MAPPINGS = {
    'ps5e' : ['u', 'i'],
    'ps5r' : ['u', 'i', 'o', 'p']
}

'''run info
'''
N_STIMS_ENC = 168
N_RUNS_ENC = 3
N_TRIALS_PER_RUN_ENC = N_STIMS_ENC // N_RUNS_ENC

N_STIMS_RET = 252
N_NEW_STIMS = 84
N_RUNS_RET = 3
N_TRIALS_PER_RUN_RET = N_STIMS_RET // N_RUNS_RET

'''stim settings
'''
ENC_BIG_STIM = 450
ENC_SMALL_STIM = 150
RET_STIM = 300

'''colors
'''
COLOR_TEXT = (0, 0, 0)
COLOR_BG = (255, 255, 255)
COLOR_EYELINK_BG = (255, 255, 255)

'''instruction strings
'''
MSG_WELCOME = "Welcome!"
MSG_LOADING = "Session loading... please wait"
MSG_CONT_PRAC = "<<< Press the touchpad to begin the practice round! >>>"
MSG_RERUN_PRAC = "Experimenter:\n\n<<< Press 'r' to complete another round of practice >>\n\n << Or, press 'c' to continue >>>"
MSG_CONT_TASK = "<<< Press the touchpad to begin >>>"
MSG_CALIB_EL = "<<< We will now calibrate the eye-tracker >>>"
MSG_BREAK = "We will now take a short break.\n\nPlease rest your eyes, and feel free to rest and move your head as you'd like.\n\nThe researcher will let you know when it's time to continue."
MSG_FINISH = "Study finished!\n\nThank you for your participation!"

'''screen/monitor settings
'''
FULLSCREEN = True
MONITOR_NAME = 'Mitsubishi Diamond Pro 2070SB'
MONITOR_WIDTH = 40 #cm
MONITOR_DISTANCE = 40 #cm
MONITOR_PX = [1024, 768]

'''task modes
'''
MODES_CB = [
    'LR',
    'RL',
]

MODES_EXP = [
    'ep',
    'rp',
    'e1',
    'r1',
    'e2',
    'r2',
    'e3',
    'r3',
    'pp',
]

MODES_EL = [
    'on',
    'off',
]

MODES_STIMSET = [
    'no',
    'yes'
]

'''data fields
'''
DATA_FIELDS = [
    'subject_id',
    'session_start',
    'phase',
    'block',
    'global_time_elapsed_secs',
    'global_trial_index',
    'raw_trial',
    'actual_stimulus_index',
    'abort_ret_trial',
    'burn_in_trial',
    'pregoal_iti_onset',
    'pregoal_iti_offset',
    'pregoal_iti_duration_secs',
    'pregoal_iti_set_time',
    'goal_onset',
    'goal_offset',
    'goal_duration_secs',
    'goal_set_time',
    'prestim_iti_onset',
    'prestim_iti_offset',
    'prestim_iti_duration_secs',
    'prestim_iti_set_time',
    'stim_onset',
    'stim_offset',
    'stim_duration_secs',
    'stim_set_time',
    'stim_file',
    'stim_old_new',
    'stim_size',
    'trigger_try_assay_again',
    'trigger_recording_start_one',
    'trigger_recording_end_one',
    'trigger_recording_duration_one',
    'trigger_recording_start_two',
    'trigger_recording_end_two',
    'trigger_recording_duration_two',
    'trigger_window_mean_one',
    'trigger_uninterpolated_window_mean_one',
    'trigger_window_mean_two',
    'trigger_uninterpolated_window_mean_two',
    'latest_baseline_mean',
    'trigger_baseline_mean',
    'trigger_baseline_std',
    'trigger_threshold_std_scale_fct',
    'trigger_lower_threshold',
    'trigger_upper_threshold',
    'trigger_should_launch',
    'trigger_actually_delivered',
    'trigger_gate_activated',
    'trigger_probdist_true_count',
    'trigger_probdist_false_count',
    'trigger_probdist_true_pct',
    'trigger_probdist_false_pct',
    'trigger_probe_onset',
    'trigger_probe_offset',
    'trigger_probe_duration',
    'null_trigger_fix_onset',
    'null_trigger_fix_offset',
    'null_trigger_fix_duration',
    'post_trigger_period_fix_onset',
    'post_trigger_period_fix_offset',
    'post_trigger_period_fix_duration',
    'blink_ctrl_circleprobe_onset',
    'blink_ctrl_circleprobe_offset',
    'blink_ctrl_circleprobe_duration',
    'enc_goal',
    'response_mapping',
    'response_key',
    'response_rt',
    'enc_response_acc',
    'ret_label',
    'screen_width',
    'screen_height',
    'screen_hz',
    'use_eyelink',
    'stimset_mode',
    'counterbalance_id',
    'experimenter',
]

EXPERIMENTERS = [
    'SS',
    'KN',
]

'''stimuli
'''
ENC_PRAC_STIMS = [
    'pepper.jpg',
    'compass.jpg',
    'redfinger.jpg',
    'thread.jpg',
    'bell.jpg',
    'coathanger.jpg',
    'tape.jpg',
    'harmonica.jpg',
]

ENC_PRAC_STIM_SIZES = ["SMALL", "BIG", "BIG", "SMALL", "BIG", "SMALL", "SMALL", "BIG"]

ENC_PRAC_GOAL_STATES = ["BGSM", "BGSM", "PLUP", "PLUP", "BGSM", "PLUP", "BGSM", "PLUP"]

RET_PRAC_STIMS = [
    'thread.jpg',
    'tape.jpg',
    'stapler.jpg',
    'pepper.jpg',
    'thimble.jpg',
    'redfinger.jpg',
    'bell.jpg',
    'compass.jpg',
]

ENC_RET_PRAC_GOAL_STATES = ["PLUP", "BGSM", "NOV", "BGSM", "NOV", "PLUP", "BGSM", "BGSM"]

RET_RET_PRAC_GOAL_STATES = ["BGSM", "PLUP", "NOV", "PLUP", "PLUP", "BGSM", "NOV", "NOV"]

RET_PRAC_ITEM_OLD_NEW = ['OLD', 'OLD', 'NEW', 'OLD', 'NEW', 'OLD', 'OLD', 'OLD']

STIM_POOL = [
    '1.jpg',
    '7.jpg',
    '8.jpg',
    '10.jpg',
    '11.jpg',
    '12.jpg',
    '14.jpg',
    '15.jpg',
    '16.jpg',
    '17.jpg',
    '18.jpg',
    '19.jpg',
    '22.jpg',
    '23.jpg',
    '24.jpg',
    '25.jpg',
    '26.jpg',
    '28.jpg',
    '29.jpg',
    '30.jpg',
    '31.jpg',
    '33.jpg',
    '34.jpg',
    '35.jpg',
    '36.jpg',
    '37.jpg',
    '38.jpg',
    '39.jpg',
    '45.jpg',
    '46.jpg',
    '49.jpg',
    '53.jpg',
    '54.jpg',
    '55.jpg',
    '56.jpg',
    '57.jpg',
    '58.jpg',
    '60.jpg',
    '61.jpg',
    '62.jpg',
    '64.jpg',
    '65.jpg',
    '66.jpg',
    '67.jpg',
    '68.jpg',
    '70.jpg',
    '71.jpg',
    '75.jpg',
    '76.jpg',
    '77.jpg',
    '78.jpg',
    '81.jpg',
    '85.jpg',
    '86.jpg',
    '87.jpg',
    '88.jpg',
    '89.jpg',
    '90.jpg',
    '91.jpg',
    '92.jpg',
    '96.jpg',
    '98.jpg',
    '101.jpg',
    '103.jpg',
    '104.jpg',
    '105.jpg',
    '106.jpg',
    '107.jpg',
    '110.jpg',
    '111.jpg',
    '112.jpg',
    '113.jpg',
    '114.jpg',
    '115.jpg',
    '116.jpg',
    '117.jpg',
    '119.jpg',
    '120.jpg',
    '121.jpg',
    '123.jpg',
    '126.jpg',
    '127.jpg',
    '128.jpg',
    '129.jpg',
    '130.jpg',
    '131.jpg',
    '132.jpg',
    '136.jpg',
    '138.jpg',
    '139.jpg',
    '141.jpg',
    '142.jpg',
    '144.jpg',
    '145.jpg',
    '146.jpg',
    '147.jpg',
    '150.jpg',
    '153.jpg',
    '154.jpg',
    '155.jpg',
    '156.jpg',
    '157.jpg',
    '158.jpg',
    '159.jpg',
    '160.jpg',
    '161.jpg',
    '162.jpg',
    '163.jpg',
    '164.jpg',
    '166.jpg',
    '169.jpg',
    '170.jpg',
    '171.jpg',
    '173.jpg',
    '174.jpg',
    '177.jpg',
    '178.jpg',
    '182.jpg',
    '183.jpg',
    '184.jpg',
    '185.jpg',
    '186.jpg',
    '187.jpg',
    '190.jpg',
    '191.jpg',
    '192.jpg',
    '193.jpg',
    '194.jpg',
    '195.jpg',
    '196.jpg',
    '197.jpg',
    '198.jpg',
    '199.jpg',
    '200.jpg',
    '201.jpg',
    '202.jpg',
    '203.jpg',
    '204.jpg',
    '205.jpg',
    '206.jpg',
    '207.jpg',
    '208.jpg',
    '209.jpg',
    '210.jpg',
    '211.jpg',
    '212.jpg',
    '214.jpg',
    '216.jpg',
    '219.jpg',
    '220.jpg',
    '221.jpg',
    '222.jpg',
    '224.jpg',
    '225.jpg',
    '226.jpg',
    '227.jpg',
    '230.jpg',
    '231.jpg',
    '232.jpg',
    '233.jpg',
    '234.jpg',
    '235.jpg',
    '236.jpg',
    '239.jpg',
    '240.jpg',
    '241.jpg',
    '243.jpg',
    '244.jpg',
    '247.jpg',
    '251.jpg',
    '252.jpg',
    '253.jpg',
    '256.jpg',
    '257.jpg',
    '258.jpg',
    '260.jpg',
    '264.jpg',
    '268.jpg',
    '269.jpg',
    '270.jpg',
    '271.jpg',
    '272.jpg',
    '273.jpg',
    '274.jpg',
    '277.jpg',
    '278.jpg',
    '279.jpg',
    '280.jpg',
    '287.jpg',
    '288.jpg',
    '291.jpg',
    '293.jpg',
    '294.jpg',
    '297.jpg',
    '303.jpg',
    '304.jpg',
    '308.jpg',
    '309.jpg',
    '310.jpg',
    '311.jpg',
    '313.jpg',
    '314.jpg',
    '317.jpg',
    '322.jpg',
    '324.jpg',
    '325.jpg',
    '327.jpg',
    '328.jpg',
    '329.jpg',
    '330.jpg',
    '332.jpg',
    '333.jpg',
    '335.jpg',
    '336.jpg',
    '338.jpg',
    '342.jpg',
    '344.jpg',
    '345.jpg',
    '347.jpg',
    '349.jpg',
    '351.jpg',
    '353.jpg',
    '355.jpg',
    '357.jpg',
    '358.jpg',
    '360.jpg',
    '363.jpg',
    '365.jpg',
    '366.jpg',
    '367.jpg',
    '369.jpg',
    '372.jpg',
    '376.jpg',
    '377.jpg',
    '382.jpg',
    '383.jpg',
    '385.jpg',
    '387.jpg',
    '389.jpg',
    '390.jpg',
    '391.jpg',
    '392.jpg',
    '394.jpg',
    '396.jpg',
    '397.jpg',
    '398.jpg',
    '400.jpg',
    '402.jpg',
    '403.jpg',
    '406.jpg',
    '407.jpg',
    '408.jpg',
    '409.jpg',
    '410.jpg',
    '411.jpg',
]

