'''Episodic Closed Loop Core Code (Real-Time)
@Version: 5.0.0
@Author: Shawn T. Schwartz
@Email: stschwartz@stanford.edu
@Date: 06/28/2023
@Links: https://shawnschwartz.com
'''

# Imports
import sys, os, random, glob, math, csv, uuid, errno, json, pickle, time, pylink, platform, re, copy
import numpy as np
import pandas as pd
import settings
from PIL import Image
from psychopy import visual, core, event, monitors, tools, data, gui, logging
from EyeLinkCoreGraphicsPsychoPy.EyeLinkCoreGraphicsPsychoPy.EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy

# Global PsychoPy Settings
logging.console.setLevel(logging.CRITICAL) # show only critical messages in the PsychoPy console

# Global convenience functions
def convert_color_value(color):
    """Converts a list of 3 values from 0 to 255 to -1 to 1.

    Parameters:
        color -- A list of 3 ints between 0 and 255 to be converted.

    Credit: https://github.com/colinquirk/templateexperiments
    """
    return [round(((n/127.5)-1), 2) for n in color]

def modify_stim_paths(stim_set, stim_dir, is_panda=False):
    """Prepends absolute image path to each stimulus image file for max compatability.

    Returns modified array with prepended absolute paths to releative paths.

    parameters:
        stim_set -- array of relative paths to stimulus image files.
        stim_dir -- absolute parent path for all stimulus files.
        is_panda -- whether this function is being applied to a pandas dataframe column.
    """
    return [os.path.join(stim_dir, i) for i in stim_set] if not is_panda else os.path.join(stim_dir, stim_set)

def validate_enc_stim_set(sequence):
    """Checks to see if encoding stim set does not have more than 4 of the same learning goals consecutively.

    Returns boolean of validation status.

    parameters:
        sequence -- array of goal states from a trial run to check
    """
    i = 4 # max set

    while i < len(sequence):
        if sequence[i] == sequence[i - 1]:
            if sequence[i] == sequence[i - 2]:
                if sequence[i] == sequence[i - 3]:
                    if sequence[i] == sequence[i - 4]:
                        return False
                    else:
                        i += 1
                else:
                    i += 2
            else:
                i += 3
        else:
            i += 4

    return True

def validate_ret_stim_set(sequence):
    """Checks to see if retrieval stim set does not have more than 4 of the same learning goals consecutively.

    Returns boolean of validation status.

    parameters:
        sequence -- array of goal states from a trial run to check
    """
    i = 3 # max set

    while i < len(sequence):
        if sequence[i] == sequence[i - 1]:
            if sequence[i] == sequence[i - 2]:
                if sequence[i] == sequence[i - 3]:
                    return False
                else:
                    i += 1
            else:
                i += 2
        else:
            i += 3

    return True

def run_enc_validation(df, num_iters_to_force_quit=5000):
    iter_counter = 0
    is_valid = False
    
    # init suffle
    df = df.sample(frac=1)

    while iter_counter < num_iters_to_force_quit and not is_valid:
        if iter_counter >= num_iters_to_force_quit:
            print("ERROR >>> Too many iterations [ " + str(iter_counter) + "] to validate quadrant orders...")
            sys.exit(1)

        is_valid = validate_enc_stim_set(list(df['enc_goal']))

        df = df.sample(frac=1) if not is_valid else df

        iter_counter += 1

    return df

def run_ret_validation(df, num_iters_to_force_quit=5000):
    iter_counter = 0
    is_valid = False
    
    # init suffle
    df = df.sample(frac=1)

    while iter_counter < num_iters_to_force_quit and not is_valid:
        if iter_counter >= num_iters_to_force_quit:
            print("ERROR >>> Too many iterations [ " + str(iter_counter) + "] to validate quadrant orders...")
            sys.exit(1)

        is_valid = validate_ret_stim_set(list(df['enc_goal']))

        df = df.sample(frac=1) if not is_valid else df

        iter_counter += 1

    return df

def check_enc_stim_set(df):
    table = pd.pivot_table(df, index=['enc_goal', 'enc_size'], aggfunc=len, fill_value=0)
    assert len(table) == 4, "Fatal assertion error: length of encoding table should be == 4... check stim set generator"
    for i_val in range(0,4):
        assert table.iloc[i_val]['enc_block'] == 14, "Fatal assertion error: invalid value not equal to 14 evaluated in counterbalanced design... check stim set generator"

def check_ret_stim_set(df):
    table = pd.pivot_table(df, index=['enc_goal'], aggfunc=len, fill_value=0)
    assert len(table) == 3, "Fatal assertion error: length of retrieval table should be == 3... check stim set generator"
    for i_val in range(0,3):
        assert table.iloc[i_val]['ret_block'] == 28, "Fatal assertion error: invalid value not equal to 28 evaluated in counterbalanced design... check stim set generator"

def remove_duplicate_pupil_samples(pupil, timestamps):
    deltas = np.diff(timestamps)
    mask = np.concatenate(([True], deltas != 0))
    masked_pupil = pupil[mask]
    return masked_pupil

def find_nan_ranges(arr):
    # Find indices where np.nan occurs
    nan_indices = np.where(np.isnan(arr))[0]

    # Initialize variables
    ranges = []
    start = None
    prev_index = None

    # Iterate through nan_indices
    for index in nan_indices:
        if start is None:
            # Start of a new range
            start = index
        elif prev_index is not None and index != prev_index + 1:
            # End of a range
            ranges.append((start, prev_index))
            start = index

        prev_index = index

    # Check if there is an open range at the end
    if start is not None and prev_index is not None:
        ranges.append((start, prev_index))

    return ranges

def pad_nans(nan_ranges, timestamps, time_threshold=100):
    left_time_id = []
    right_time_id = []

    for i_range in nan_ranges:
        left_index = i_range[0]
        right_index = i_range[1]

        # solve edge case with left_index being 0
        if left_index == 0:
            left_time_id.append(0)
        
        starting_left_time = timestamps[left_index]
        for left_id, left_side in reversed(list(enumerate(list(range(left_index))))):
            current_left_time = timestamps[left_side]
            time_delta = starting_left_time - current_left_time
            if time_delta > time_threshold or left_id == 0:
                left_time_id.append(left_side)
                break
            
        starting_right_time = timestamps[right_index]
        for right_id, right_side in enumerate(list(range(right_index, len(timestamps)))):
            current_right_time = timestamps[right_side]
            time_delta = current_right_time - starting_right_time
            if (time_delta > time_threshold) or (right_side == len(timestamps) - 1):
                right_time_id.append(right_side)
                break
                
    return left_time_id, right_time_id

def pad_interpolate_nans(pupils, left_time_id, right_time_id):
    x = copy.deepcopy(pupils)

    print("left_time_id_len: " + str(len(left_time_id)))
    print("right_time_id_len: " + str(len(right_time_id)))

    assert len(left_time_id) == len(right_time_id), "Error: time_id arrays are not the same length!"

    for i in range(len(left_time_id)):
        left_min = left_time_id[i]
        right_max = right_time_id[i]
        x[left_min:right_max + 1] = [np.nan] * (right_max - left_min + 1)
        
    return x

class EpisodicClosedLoop():
    def __init__(self, experiment_name, stim_directory, data_directory, *args, **kwargs):
        super(EpisodicClosedLoop, self).__init__(*args, **kwargs)

        self.experiment_name = experiment_name
        self.stim_directory = stim_directory
        self.data_directory = data_directory
        self.data_fields = settings.DATA_FIELDS

        self.enc_pregoal_iti = settings.ENC_PREGOAL_ITI * settings.DEMO_RATE
        self.enc_goal = settings.ENC_GOAL * settings.DEMO_RATE
        self.enc_preprobe_iti = settings.ENC_PREPROBE_ITI * settings.DEMO_RATE
        self.enc_probe = settings.ENC_PROBE * settings.DEMO_RATE

        self.ret_preprobe_iti = settings.RET_PREPROBE_ITI * settings.DEMO_RATE
        self.ret_probe = settings.RET_PROBE * settings.DEMO_RATE
        
        self.reorienting_probe_time = settings.REORIENTING_PROBE_TIME
        self.reorienting_probe_error = settings.REORIENTING_PROBE_ERROR
        self.reorienting_flicker_rate = settings.REORIENTING_FLICKER_RATE
        self.trigger_window_max_time = settings.TRIGGER_WINDOW_MAX_TIME
        self.post_trigger_fix_window_time = settings.POST_TRIGGER_FIX_WINDOW_TIME
        self.post_trigger_p1_epoch_time = settings.POST_TRIGGER_P1_EPOCH_TIME
        self.sd_trigger_scale = settings.SD_TRIGGER_SCALE
        self.ctrl_probe_contig_limit = settings.CTRL_PROBE_CONTIG_LIMIT
        self.missing_data_tolerance = settings.MISSING_DATA_TOLERANCE
        
        self.LATEST_REALTIME_PUPIL = None
        self.LATEST_REALTIME_PUPIL_TS = None
        self.REALTIME_BLOCKWISE_PUPIL_MEANS = None
        self.REALTIME_BLOCKWISE_PUPIL_STDS = None
        
        self.participant_baseline_mean = None
        self.participant_baseline_std = None
        self.participant_threshold_lower_bound = None
        self.participant_threshold_upper_bound = None

        self.enc_conceptual_goal = settings.ENC_CONCEPTUAL_GOAL
        self.enc_perceptual_goal = settings.ENC_PERCEPTUAL_GOAL

        self.ret_conceptual_goal = settings.RET_CONCEPTUAL_GOAL
        self.ret_perceptual_goal = settings.RET_PERCEPTUAL_GOAL
        self.ret_novel_goal = settings.RET_NOVEL_GOAL

        self.response_key_mappings = settings.RESPONSE_KEY_MAPPINGS
        self.response_keys = None

        self.n_stims_enc = settings.N_STIMS_ENC
        self.n_runs_enc = settings.N_RUNS_ENC
        self.n_trials_per_run_enc = settings.N_TRIALS_PER_RUN_ENC

        self.n_stims_ret = settings.N_STIMS_RET
        self.n_new_stims = settings.N_NEW_STIMS
        self.n_runs_ret = settings.N_RUNS_RET
        self.n_trials_per_run_ret = settings.N_TRIALS_PER_RUN_RET

        self.enc_big_stim = settings.ENC_BIG_STIM
        self.enc_small_stim = settings.ENC_SMALL_STIM
        self.ret_stim = settings.RET_STIM

        self.enc_prac_stim_sizes = settings.ENC_PRAC_STIM_SIZES
        self.enc_prac_goal_states = settings.ENC_PRAC_GOAL_STATES
        self.enc_ret_prac_goal_states = settings.ENC_RET_PRAC_GOAL_STATES
        self.ret_ret_prac_goal_states = settings.RET_RET_PRAC_GOAL_STATES
        self.ret_prac_item_old_new = settings.RET_PRAC_ITEM_OLD_NEW

        self.enc_prac_stims = modify_stim_paths(settings.ENC_PRAC_STIMS, self.stim_directory)
        self.ret_prac_stims = modify_stim_paths(settings.RET_PRAC_STIMS, self.stim_directory)
        self.stim_pool = modify_stim_paths(settings.STIM_POOL, self.stim_directory)

        self.color_text = convert_color_value(settings.COLOR_TEXT)
        self.color_bg = convert_color_value(settings.COLOR_BG)
        self.color_eyelink_bg = convert_color_value(settings.COLOR_EYELINK_BG)

        self.msg_welcome = settings.MSG_WELCOME
        self.msg_loading = settings.MSG_LOADING
        self.msg_cont_prac = settings.MSG_CONT_PRAC
        self.msg_rerun_prac = settings.MSG_RERUN_PRAC
        self.msg_cont_task = settings.MSG_CONT_TASK
        self.msg_calib_el = settings.MSG_CALIB_EL
        self.msg_break = settings.MSG_BREAK
        self.msg_finish = settings.MSG_FINISH

        self.modes_exp = settings.MODES_EXP
        self.modes_el = settings.MODES_EL
        self.modes_cb = settings.MODES_CB
        self.modes_stimset = settings.MODES_STIMSET
        self.experimenters = settings.EXPERIMENTERS

        self.monitor_name = settings.MONITOR_NAME
        self.monitor_width = settings.MONITOR_WIDTH
        self.monitor_distance = settings.MONITOR_DISTANCE
        self.monitor_px = settings.MONITOR_PX
        self.fullscreen = settings.FULLSCREEN

        self.experiment_data = []
        self.experiment_data_filename = None
        self.data_lines_written = 0
        self.experiment_info = {}
        self.experiment_window = None
        self.screen_hz = None

        self.eyetrack = False
        self.trial_index = 0

        self.overwrite_ok = None

        self.session_timestamp = time.strftime("%m-%d-%Y_%H%M%S")

        self.experiment_monitor = monitors.Monitor(
            self.monitor_name,
            width = self.monitor_width,
            distance = self.monitor_distance)
        self.experiment_monitor.setSizePix(self.monitor_px)

        self.elapsed_time_clock = None

        vars(self).update(kwargs)

    """Task window and data management functions
    """
    @staticmethod
    def _confirm_overwrite():
        """
        https://github.com/colinquirk/templateexperiments
        """
        overwrite_dlg = gui.Dlg(
            'Overwrite?', labelButtonOK='Overwrite',
            labelButtonCancel='New File')
        overwrite_dlg.addText('File already exists. Overwrite?')
        overwrite_dlg.show()

        return overwrite_dlg.OK

    def validate_fname(self, fname, ext=".csv"):
        if os.path.isfile(fname + ext):
            if self.overwrite_ok is None:
                self.overwrite_ok = self._confirm_overwrite()

            if not self.overwrite_ok:
                i = 1
                new_fname = fname + '(' + str(i) + ')'
                while os.path.isfile(new_fname + ext):
                    i += 1
                    new_fname = fname + '(' + str(i) + ')'
                fname = new_fname
        fname += ext

        return fname

    def open_window(self, **kwargs):
        """Opens the psychopy window.
        """
        self.experiment_window = visual.Window(
            monitor = self.experiment_monitor, 
            fullscr = self.fullscreen, 
            color = self.color_bg, 
            winType = 'pyglet',
            colorSpace = 'rgb', 
            units = 'pix',
            allowGUI = False, 
            **kwargs)
    
    def get_experiment_info(self):
        self.experiment_info = { 
                                 'Subject Number': '',
                                 'CB': self.modes_cb,
                                 'UES': self.modes_stimset,
                                 'EP': self.modes_exp,
                                 'EyeLink': self.modes_el,
                                 'EyeLink IP': '100.1.1.1',
                                 'Experimenter Initials': self.experimenters,
                                }
                                 
        exp_info = gui.DlgFromDict(
            self.experiment_info,
            title = self.experiment_name,
            order = ['Subject Number',
                     'CB',
                     'UES',
                     'EP',
                     'EyeLink',
                     'EyeLink IP',
                     'Experimenter Initials',
                   ]
        )
        
        return exp_info.OK

    def make_subject_dir(self):
        if not os.path.exists(os.path.join(self.experiment_info['Subject Number'])):
            os.makedirs(os.path.join(self.experiment_info['Subject Number']))

    def chdir(self):
        """https://github.com/colinquirk/PsychopyResolutionWR
        """
        try:
            os.makedirs(self.data_directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        os.chdir(self.data_directory)
        
    def send_data(self, data):
        """https://github.com/colinquirk/PsychopyResolutionWR
        """
        
        self.update_experiment_data(data)
            
    def open_csv_data_file(self, entry_point, block_num, data_filename=None):
        """Adapted from: https://github.com/colinquirk/PsychopyResolutionWR
        """
        if not os.path.exists(os.path.join(self.data_directory, self.experiment_info['Subject Number'], 'behavior')):
            os.makedirs(os.path.join(self.data_directory, self.experiment_info['Subject Number'], 'behavior'))

        if not os.path.exists(os.path.join(self.data_directory, self.experiment_info['Subject Number'], 'eyetracking')):
            os.makedirs(os.path.join(self.data_directory, self.experiment_info['Subject Number'], 'eyetracking'))
            
        if not os.path.exists(os.path.join(self.data_directory, self.experiment_info['Subject Number'], 'encoding_pupil')):
            os.makedirs(os.path.join(self.data_directory, self.experiment_info['Subject Number'], 'encoding_pupil'))
            
        if not os.path.exists(os.path.join(self.data_directory, self.experiment_info['Subject Number'], 'retrieval_pupil')):
            os.makedirs(os.path.join(self.data_directory, self.experiment_info['Subject Number'], 'retrieval_pupil'))
        
        # write out real time encoding pupil pickle files dir
        pickle_dir = None
        if entry_point == "enc":
            pickle_dir_parent = "encoding_pupil"
        elif entry_point == "ret":
            pickle_dir_parent = "retrieval_pupil"
            
        if entry_point in ("enc", "ret"):
            pickle_dir = os.path.join(self.experiment_info['Subject Number'], pickle_dir_parent, str(entry_point) + str(block_num))
        
            if os.path.exists(pickle_dir):
                i = 1
                new_pickle_dir = pickle_dir + '(' + str(i) + ')'
                while os.path.exists(new_pickle_dir):
                    i += 1
                    new_pickle_dir = pickle_dir + '(' + str(i) + ')'
                pickle_dir = new_pickle_dir

            os.makedirs(pickle_dir)

        # now do the data csv files for behavior
        if data_filename is None:
            data_filename = os.path.join(self.experiment_info['Subject Number'], 'behavior', self.experiment_info['Subject Number'] + '_' + self.experiment_info['CB'] + '-' + str(entry_point) + str(block_num) + '.csv')
        elif data_filename[-4:] == '.csv':
            data_filename = data_filename[:-4]

        if os.path.isfile(data_filename):
            i = 1
            new_filename = data_filename[:-4] + '(' + str(i) + ')' + '.csv'
            while os.path.isfile(new_filename):
                i += 1
                new_filename = data_filename[:-4] + '(' + str(i) + ')' + '.csv'
            data_filename = new_filename

        self.experiment_data_filename = data_filename

        # Write the header
        with open(self.experiment_data_filename, 'w+') as data_file:
            for field in self.data_fields:
                data_file.write('"')
                data_file.write(field)
                data_file.write('"')
                if field != self.data_fields[-1]:
                    data_file.write(',')
            data_file.write('\n')
            
        return pickle_dir
            
    def save_data_to_csv(self):
        """https://github.com/colinquirk/templateexperiments
        """

        with open(self.experiment_data_filename, 'a') as data_file:
            for trial in range(
                    self.data_lines_written, len(self.experiment_data)):
                for field in self.data_fields:
                    data_file.write('"')
                    try:
                        data_file.write(
                            str(self.experiment_data[trial][field]))
                    except KeyError:
                        data_file.write('NA')
                    data_file.write('"')
                    if field != self.data_fields[-1]:
                        data_file.write(',')
                data_file.write('\n')

        self.data_lines_written = len(self.experiment_data)
        
    def update_experiment_data(self, new_data):
        """https://github.com/colinquirk/templateexperiments
        """
        if not isinstance(new_data, list):
            raise TypeError('Experiment data must be type list.')

        self.experiment_data.extend(new_data)

    """Eyelink helper functions
    """
    def _swap_bg_color_to_calibration_screen(self):
        self.experiment_window.color = self.color_eyelink_bg
        self.experiment_window.flip()

    def _swap_bg_color_to_task_screen(self):
        self.experiment_window.color = self.color_bg
        self.experiment_window.flip()

    def _connect_eyelink(self):
        try:
            self.el_tracker = pylink.EyeLink(self.experiment_info['EyeLink IP'])
        except RuntimeError as error:
            print('ERROR:', error)
            self.experiment_window.close()
            sys.exit(1)

    def _open_edf_file(self, phase, block):
        self.edf_file = str(self.experiment_info['Subject Number'][0:4] + phase[0:1] + str(block) + 'c' + '.EDF')

        try:
            self.el_tracker.openDataFile(self.edf_file)
        except RuntimeError as err:
            print('ERROR:', err)
            # close the link if one is open
            if self.el_tracker.isConnected():
                self.el_tracker.close()
            self.experiment_window.close()
            sys.exit(1)

    def _send_edf_preamble(self):
        preamble_text = 'RECORDED BY %s' % os.path.basename(__file__)
        self.el_tracker.sendCommand("add_file_preamble_text '%s'" % preamble_text)

    def _config_eyelink(self):
        self.el_tracker.setOfflineMode() # put the tracker in offline mode before tracking parameters are changed
        eyelink_ver = 0
        vstr = self.el_tracker.getTrackerVersionString()
        eyelink_ver = int(vstr.split()[-1].split('.')[0])
        print('Running experiment on %s, version %d' % (vstr, eyelink_ver))

        file_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT'
        link_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT'

        if eyelink_ver > 3:
            file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT'
            link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT'
        else:
            file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,GAZERES,BUTTON,STATUS,INPUT'
            link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,INPUT'
        self.el_tracker.sendCommand("file_event_filter = %s" % file_event_flags)
        self.el_tracker.sendCommand("file_sample_data = %s" % file_sample_flags)
        self.el_tracker.sendCommand("link_event_filter = %s" % link_event_flags)
        self.el_tracker.sendCommand("link_sample_data = %s" % link_sample_flags)

        if eyelink_ver > 2:
            self.el_tracker.sendCommand("sample_rate 1000")

        self.el_tracker.sendCommand("calibration_type = HV5")
        self.el_tracker.sendCommand("randomize_calibration_order = NO")
        self.el_tracker.sendCommand("calibration_area_proportion 1.0 1.0")
        self.el_tracker.sendCommand("validation_area_proportion 0.6 0.6")

        self.el_tracker.sendCommand("button_function 5 'accept_target_fixation'")

        # get the native screen resolution used by psychopy
        scn_width = int(self.experiment_window.size[0])
        scn_height = int(self.experiment_window.size[1])

        # pass the display pixel coordinates (left, top, right, bottom) to the tracker
        el_coords = "screen_pixel_coords = 0.0, 0.0, %d, %d" % (scn_width, scn_height)
        self.el_tracker.sendCommand(el_coords)

        # write a DISPLAY_COORDS message to the EDF file
        dv_coords = "DISPLAY_COORDS 0 0 %d %d" % (scn_width, scn_height)
        self.el_tracker.sendMessage(dv_coords)

        calib_x0 = 212
        calib_x1 = 512
        calib_x2 = 812
        calib_y0 = 134
        calib_y1 = 384
        calib_y2 = 634

        calib_positions = "calibration_targets = %d,%d %d,%d %d,%d %d,%d %d,%d" % (
            calib_x1, calib_y1,
            calib_x1, calib_y0,
            calib_x1, calib_y2,
            calib_x0, calib_y1,
            calib_x2, calib_y1)
        self.el_tracker.sendCommand(calib_positions)

    def _calibrate_eyelink(self):
        self._swap_bg_color_to_calibration_screen()
        self.make_message(self.msg_calib_el)
        genv = EyeLinkCoreGraphicsPsychoPy(self.el_tracker, self.experiment_window)
        pylink.openGraphicsEx(genv)
        self.el_tracker.doTrackerSetup()

    def _start_eyelink_recording(self):
        self.el_tracker.startRecording(1, 1, 1, 1)
        time.sleep(.1)  # required
        self.el_tracker.sendMessage('start_run')
        self._swap_bg_color_to_task_screen()

    def trigger_eyelink(self, phase, block):
        self._connect_eyelink()
        self._open_edf_file(phase, block)
        self._send_edf_preamble()
        self._config_eyelink()
        self._calibrate_eyelink()
        self._start_eyelink_recording()

    def disconnect_eyelink(self):
        self.el_tracker.sendMessage('end_run')
        if self.el_tracker.isConnected():
            time.sleep(.1)  # required
            self.el_tracker.stopRecording()
            self.el_tracker.setOfflineMode() # put the tracker into offline mode
            self.el_tracker.sendCommand('clear_screen 0') # clear the host pc screen and wait for 500 ms
            pylink.msecDelay(500)
            self.el_tracker.closeDataFile() # close the EDF data file on the host pc
            pylink.closeGraphics()
            self.el_tracker.close() # disconnect the tracker
    
    """Real time pupillometry functions
    """
    def RealTimeTrigger(self, trial=None, stim=None, is_burn_in_trial=False):
        pupil_samples = []
        pupil_timestamps = []
        pupil_samples_two = []
        pupil_timestamps_two = []
        
        try_assay_again = False
        
        trigger_recording_start = None
        trigger_recording_start_two = None    
        trigger_recording_end = None
        trigger_recording_end_two = None
        trigger_recording_duration = None
        trigger_recording_duration_two = None
        launch_trigger = False
        activate_trigger_gate = False
        window_mean = None
        window_mean_two = None
        trigger_probe_onset = None
        trigger_probe_offset = None
        trigger_probe_duration = None
        null_trigger_fix_onset = None
        null_trigger_fix_offset = None
        null_trigger_fix_duration = None
        should_launch_real_trigger = False
        uninterpolated_window_mean = None
        uninterpolated_window_mean_two = None
        interpolated_pupil_one = None
        interpolated_pupil_two = None
        
        if self.eyetrack:
            live_trigger_sampling_timer = core.CountdownTimer(self.trigger_window_max_time)
            trigger_recording_start = self.elapsed_run_clock.getTime()
            stim_basename = os.path.basename(stim)
            self.el_tracker.sendMessage('RTCLR1_S %s' % (stim_basename))

            while live_trigger_sampling_timer.getTime() >= 0:
                # get and store latest pupil samples from tracker
                cur_pupil, cur_time = self.GetPupilSize()

                pupil_samples.append(cur_pupil)
                pupil_timestamps.append(cur_time)
                time.sleep(1 / 1000)
            
            # compute prop of nans
            prop_nan_realtime = np.count_nonzero(np.isnan(pupil_samples)) / len(pupil_samples)

            if prop_nan_realtime < self.missing_data_tolerance:
                nan_ranges_one = find_nan_ranges(pupil_samples)
                padded_pupil_id_left_one, padded_pupil_id_right_one = pad_nans(nan_ranges_one, pupil_timestamps)
                interpolated_pupil_one = pad_interpolate_nans(pupil_samples, padded_pupil_id_left_one, padded_pupil_id_right_one)
                window_mean = np.nanmean(interpolated_pupil_one)
                uninterpolated_window_mean = np.nanmean(pupil_samples)
            else:
                window_mean = 'blink'
                try_assay_again = True

            trigger_recording_end = self.elapsed_run_clock.getTime()
            trigger_recording_duration = trigger_recording_end - trigger_recording_start
            stim_basename = os.path.basename(stim)
            self.el_tracker.sendMessage('RTCLR1_E %s' % (stim_basename))
            
            if window_mean == 'blink':
                if self.trigger_window_max_time - trigger_recording_duration > 0:
                    core.wait(self.trigger_window_max_time - trigger_recording_duration)
            
            # check if mean exceeds baseline thresholds
            if (not is_burn_in_trial) and (window_mean != 'blink'):
                if ((window_mean > self.participant_threshold_upper_bound) or (window_mean < self.participant_threshold_lower_bound)):
                    launch_trigger = True
                else:
                    try_assay_again = True
                    
            # determine and launch second real-time assay (if needed)
            if try_assay_again or is_burn_in_trial:
                live_trigger_sampling_timer_two = core.CountdownTimer(self.trigger_window_max_time)
                trigger_recording_start_two = self.elapsed_run_clock.getTime()
                stim_basename = os.path.basename(stim)
                self.el_tracker.sendMessage('RTCLR2_S %s' % (stim_basename))
                
                while live_trigger_sampling_timer_two.getTime() >= 0:
                    # get and store latest pupil samples from tracker
                    cur_pupil_two, cur_time_two = self.GetPupilSize()

                    pupil_samples_two.append(cur_pupil_two)
                    pupil_timestamps_two.append(cur_time_two)
                    time.sleep(1 / 1000)
                
                # compute prop of nans
                prop_nan_realtime_two = np.count_nonzero(np.isnan(pupil_samples_two)) / len(pupil_samples_two)

                if prop_nan_realtime_two < self.missing_data_tolerance:
                    nan_ranges_two = find_nan_ranges(pupil_samples_two)
                    padded_pupil_id_left_two, padded_pupil_id_right_two = pad_nans(nan_ranges_two, pupil_timestamps_two)
                    interpolated_pupil_two = pad_interpolate_nans(pupil_samples_two, padded_pupil_id_left_two, padded_pupil_id_right_two)
                    window_mean_two = np.nanmean(interpolated_pupil_two)
                    uninterpolated_window_mean_two = np.nanmean(pupil_samples_two)
                else:
                    window_mean_two = 'blink'

                trigger_recording_end_two = self.elapsed_run_clock.getTime()
                trigger_recording_duration_two = trigger_recording_end_two - trigger_recording_start_two
                stim_basename = os.path.basename(stim)
                self.el_tracker.sendMessage('RTCLR2_E %s' % (stim_basename))
                
                if window_mean_two == 'blink':
                    if self.trigger_window_max_time - trigger_recording_duration_two > 0:
                        core.wait(self.trigger_window_max_time - trigger_recording_duration_two)
            
                # check if mean exceeds baseline thresholds
                if (not is_burn_in_trial) and (window_mean_two != 'blink'):
                    if ((window_mean_two > self.participant_threshold_upper_bound) or (window_mean_two < self.participant_threshold_lower_bound)):
                        launch_trigger = True
        
        # (2) based on real-time assay, either deliver reorienting probe or just replace with the static fixation cross      
        # launch_trigger = True ##DIAGNOSTIC MANUAL MODE -- TURN ON TRIGGERING FOR ALL TRIALS
        # if True in self.trigger_delivery_history[-2:]:
        #     activate_trigger_gate = True

        if launch_trigger and not is_burn_in_trial and not activate_trigger_gate:
            if self.NEXT_should_launch_real_trigger is None:
                should_launch_real_trigger = random.choice([True, False])
            
                # update prob dist counts
                if should_launch_real_trigger:
                    self.trigger_true_count += 1
                else:
                    self.trigger_false_count += 1
                    
                # calculate current distribution
                true_percentage = (self.trigger_true_count / (self.trigger_true_count + self.trigger_false_count)) * 100
                false_percentage = (self.trigger_false_count / (self.trigger_true_count + self.trigger_false_count)) * 100
                
                # adjust distribution if necessary
                if true_percentage > 50:
                    self.NEXT_should_launch_real_trigger = False
                elif false_percentage > 50:
                    self.NEXT_should_launch_real_trigger = True
            elif self.NEXT_should_launch_real_trigger is not None:
                # calculate current distribution
                true_percentage = (self.trigger_true_count / (self.trigger_true_count + self.trigger_false_count)) * 100
                false_percentage = (self.trigger_false_count / (self.trigger_true_count + self.trigger_false_count)) * 100
                
                if true_percentage == 50:
                    should_launch_real_trigger = random.choice([True, False])
                else:
                    should_launch_real_trigger = self.NEXT_should_launch_real_trigger
                    
                # update prob dist counts
                if should_launch_real_trigger:
                    self.trigger_true_count += 1
                else:
                    self.trigger_false_count += 1
                    
                # calculate current distribution
                true_percentage = (self.trigger_true_count / (self.trigger_true_count + self.trigger_false_count)) * 100
                false_percentage = (self.trigger_false_count / (self.trigger_true_count + self.trigger_false_count)) * 100
                
                # adjust distribution if necessary
                if true_percentage > 50:
                    self.NEXT_should_launch_real_trigger = False
                elif false_percentage > 50:
                    self.NEXT_should_launch_real_trigger = True
                    
            self.trigger_true_current_pct = true_percentage
            self.trigger_false_current_pct = false_percentage    
        
        if should_launch_real_trigger and not is_burn_in_trial:
            trigger_probe_onset, trigger_probe_offset = self.make_reorienting_probe(self.reorienting_probe_time, stim=stim, send_eyelink_message=True)
            trigger_probe_duration = trigger_probe_offset - trigger_probe_onset
        
        if not should_launch_real_trigger:
            null_trigger_fix_onset, null_trigger_fix_offset = self.make_fixation(self.reorienting_probe_time + self.reorienting_probe_error, trial=trial, stim=stim, send_eyelink_message=True, is_dud_trigger=True)
            null_trigger_fix_duration = null_trigger_fix_offset - null_trigger_fix_onset
            
        # (3) after trigger/no-trigger period, replace back to normal fixation cross and capture more real-time pupil metrics
        # change message if blink during real-time window two
        if window_mean_two == 'blink':
            post_trig_eyelink_message = 'POSTTRIG_BLINK'
        else:
            post_trig_eyelink_message = 'POSTTRIG'

        post_trigger_period_fix_onset, post_trigger_period_fix_offset = self.make_fixation(self.post_trigger_fix_window_time, phase="ret", trial=trial, stim=stim, send_eyelink_message=True, message_flag=post_trig_eyelink_message, is_post_ret_probe_fixation=True)

        # save out the raw (p0) pupil and timestamps arrays
        if trial < 10:
            f_prefix = '000'
        elif trial >= 10 and trial < 100:
            f_prefix = '00'
        elif trial >= 100:
            f_prefix = '0'
        cur_pupils_pickle_filename = os.path.join(self.cur_pupil_pickle_dir, "p0_pupil_raw_1_" + f_prefix + str(trial) + '_' + os.path.basename(stim)[:-4] + '.pickle')
        pupils_p0_np = np.asarray(pupil_samples)
        with open(cur_pupils_pickle_filename, 'wb') as handle:
            pickle.dump(pupils_p0_np, handle, protocol=pickle.HIGHEST_PROTOCOL)
            
        cur_pupils_pickle_filename = os.path.join(self.cur_pupil_pickle_dir, "p0_pupil_raw_2_" + f_prefix + str(trial) + '_' + os.path.basename(stim)[:-4] + '.pickle')
        pupils_p0_np = np.asarray(pupil_samples_two)
        with open(cur_pupils_pickle_filename, 'wb') as handle:
            pickle.dump(pupils_p0_np, handle, protocol=pickle.HIGHEST_PROTOCOL)

        cur_pupils_pickle_filename = os.path.join(self.cur_pupil_pickle_dir, "p0_pupil_interp_1_" + f_prefix + str(trial) + '_' + os.path.basename(stim)[:-4] + '.pickle')
        pupils_p0_np = np.asarray(interpolated_pupil_one)
        with open(cur_pupils_pickle_filename, 'wb') as handle:
            pickle.dump(pupils_p0_np, handle, protocol=pickle.HIGHEST_PROTOCOL)
            
        cur_pupils_pickle_filename = os.path.join(self.cur_pupil_pickle_dir, "p0_pupil_interp_2_" + f_prefix + str(trial) + '_' + os.path.basename(stim)[:-4] + '.pickle')
        pupils_p0_np = np.asarray(interpolated_pupil_two)
        with open(cur_pupils_pickle_filename, 'wb') as handle:
            pickle.dump(pupils_p0_np, handle, protocol=pickle.HIGHEST_PROTOCOL)
            
        cur_pupils_pickle_filename = os.path.join(self.cur_pupil_pickle_dir, "p0_ts_1_" + f_prefix + str(trial) + '_' + os.path.basename(stim)[:-4] + '.pickle')
        pupils_p0_ts_np = np.asarray(pupil_timestamps)
        with open(cur_pupils_pickle_filename, 'wb') as handle:
            pickle.dump(pupils_p0_ts_np, handle, protocol=pickle.HIGHEST_PROTOCOL)
            
        cur_pupils_pickle_filename = os.path.join(self.cur_pupil_pickle_dir, "p0_ts_2_" + f_prefix + str(trial) + '_' + os.path.basename(stim)[:-4] + '.pickle')
        pupils_p0_ts_np = np.asarray(pupil_timestamps_two)
        with open(cur_pupils_pickle_filename, 'wb') as handle:
            pickle.dump(pupils_p0_ts_np, handle, protocol=pickle.HIGHEST_PROTOCOL)
           
        return window_mean, launch_trigger, should_launch_real_trigger, trigger_recording_start, trigger_recording_end, trigger_recording_duration, trigger_probe_onset, trigger_probe_offset, trigger_probe_duration, null_trigger_fix_onset, null_trigger_fix_offset, null_trigger_fix_duration, post_trigger_period_fix_onset, post_trigger_period_fix_offset, activate_trigger_gate, try_assay_again, window_mean_two, trigger_recording_start_two, trigger_recording_end_two, trigger_recording_duration_two, uninterpolated_window_mean, uninterpolated_window_mean_two
    
    def GetPupilSize(self):
        # determine which eye is being tracked
        if self.el_tracker is not None:
            eye = self.el_tracker.eyeAvailable()
            # if both eyes are present: use right eye only
            if eye == 2:
                eye = 1
                
            # check for new sample update
            dt = self.el_tracker.getNewestSample() 

            # gets the gaze position of the latest sample
            if(dt != None):
                if eye == 0:
                    size_left = dt.getLeftEye().getPupilSize()
                    time_left = dt.getTime()
                    if size_left == 0:
                        size_left = np.nan
                    size_right = np.nan
                elif eye == 1:
                    size_right = dt.getRightEye().getPupilSize()
                    time_right = dt.getTime()
                    size_left = np.nan
                    if size_right == 0:
                        size_right = np.nan
                elif eye == 2:
                    size_left = dt.getLeftEye().getPupilSize()
                    size_right = dt.getRightEye().getPupilSize()
                    time_both = dt.getTime()
                    if size_left == 0:
                        size_left = np.nan
            else:
                size_left = np.nan

            return size_right, time_right
    
    def InterpolateNaNs(self, pupil_np):
        # check proportion of NaNs (reject if > 50%)
        prop_nan = np.count_nonzero(np.isnan(pupil_np)) / len(pupil_np)
        if prop_nan > .5:
            return [np.nan] * len(pupil_np)
        
        # if retained, then interpolate
        pupil_pd = pd.Series(pupil_np)
        pupil_pd = pupil_pd.interpolate(method="linear", axis=0, inplace=False)
        pupil_pd.fillna(method="bfill", inplace=True)
        pupil_pd.fillna(method="ffill", inplace=True)
        
        return np.array(pupil_pd)

    def PostProcConvertTrialLevelPickles(self):
        # get real-time pupil files from retrieval periods (p0 and p1)
        subdirectories = ["ret1", "ret2", "ret3"]
        pupil_periods = ["p0_pupil_interp_1_", "p0_pupil_interp_2_", "p0_pupil_raw_1_", "p0_pupil_raw_2_", "p1_pupil_", "2s-baseline_pupil_"]
        
        for pupil_period in pupil_periods:
            pupil_files_pattern = os.path.join(self.experiment_info['Subject Number'], 'retrieval_pupil', '**', pupil_period + '*.pickle')
            pupil_files = [file for file in glob.glob(pupil_files_pattern, recursive=True) if any(subdir in file for subdir in subdirectories)]
            
            # collapse pickles into a dataframe
            all_raw_pupils_collapsed = []
            all_timeseries_collapsed = []
            all_epochs_description = []
            all_assay_description = []
            for pupil_file in pupil_files:
                if pupil_period in ("p1_pupil_", "2s-baseline_pupil_"):
                    timeseries_file = re.sub(r"pupil_", "ts_", pupil_file)
                else:    
                    timeseries_file = re.sub(r"pupil_(interp|raw)_", "ts_", pupil_file)
                with open(pupil_file, 'rb') as pupil_f, open(timeseries_file, 'rb') as timeseries_f:
                    # load raw pupil and corresponding timeseries arrays from pickles
                    raw_trial_level_pupil = pickle.load(pupil_f)
                    raw_trial_level_pupil_timeseries = pickle.load(timeseries_f)
                    
                    # compile raw pupil / timeseries
                    all_raw_pupils_collapsed.append(raw_trial_level_pupil)
                    all_timeseries_collapsed.append(raw_trial_level_pupil_timeseries)
                    all_epochs_description.append(pupil_file)
                    all_assay_description.append(pupil_period)
                    
            # save out loaded epochs
            pupil_epoch_data = []
            for raw_pupil_arr, timeseries_arr, description_string, assay_string in zip(all_raw_pupils_collapsed, all_timeseries_collapsed, all_epochs_description, all_assay_description):
                # handle 0-d array edge case
                if raw_pupil_arr.ndim == 0:
                    raw_pupil_arr = []
                    raw_pupil_arr.append(np.nan)
                for pupil_element, timeseries_element in zip(raw_pupil_arr, timeseries_arr):
                    pupil_epoch_data.append((assay_string, description_string, pupil_element, timeseries_element))
                    
            pupil_epoch_df = pd.DataFrame(pupil_epoch_data, columns=['assay', 'trial', 'pupil', 'time'])
            pupil_epoch_df.to_csv(os.path.join(self.experiment_info['Subject Number'], 'session', pupil_period + 'realtime_ret_epochs.csv'), index=False)
            
    """Custom task helper functions
    """
    def _make_blank_screen(self):
        blank = visual.TextStim(win=self.experiment_window, colorSpace='rgb255', color=self.color_bg, bold=False, text=' ', height=67, pos=[0,0])
        blank.draw()
        self.experiment_window.flip()
        core.wait(1.5)

    def make_message(self, message_string, key_list=['space']):
        message = visual.TextStim(win=self.experiment_window, colorSpace='rgb255', font='Times', color=self.color_text, text=message_string)
        message.draw()
        self.experiment_window.flip()
        if key_list is not None:
            keys = event.waitKeys(keyList=key_list)
            return keys

    def _make_blank_fixation(self, duration=2):
        fix_size = 36
        fixation = visual.TextStim(win=self.experiment_window, colorSpace='rgb255', font='Times', color=self.color_text, bold=False, text='+', height=fix_size, pos=[0,0])
        fixation.draw()
        self.experiment_window.flip()
        core.wait(duration)

    def make_fixation(self, duration, phase=None, trial=None, stim=None, message_flag=None, send_eyelink_message=False, is_dud_trigger=False, is_post_ret_probe_fixation=False, raw_trial=None):
        pupils = []
        pupils_ts = []

        pupils_p1 = []
        pupils_p1_ts = []

        fix_size = 36
        fixation = visual.TextStim(win=self.experiment_window, colorSpace='rgb255', font='Times', color=self.color_text, bold=False, text='+', height=fix_size, pos=[0,0])
        fixation.draw()
        self.experiment_window.flip()
        onset = self.elapsed_run_clock.getTime()
        if self.eyetrack and send_eyelink_message:
            stim_basename = os.path.basename(stim)
            if is_dud_trigger:
                self.el_tracker.sendMessage('DUDTRIG %s' % (stim_basename))
            else:
                self.el_tracker.sendMessage('FIX_%s %s' % (message_flag, stim_basename))
        
        # store baseline pupil epochs during last 2 seconds of the entire 4 secs of each pre-stim ITI @retrieval
        if phase == "ret" and message_flag == "PRESTIM":
            recording_period_s = 2
            core.wait(duration-recording_period_s)
            live_pupil_sampling_timer = core.CountdownTimer(recording_period_s)
            if self.eyetrack:
                while live_pupil_sampling_timer.getTime() >= 0:
                    cur_pupil, cur_time = self.GetPupilSize()
                    pupils.append(cur_pupil)
                    pupils_ts.append(cur_time)
                    time.sleep(1 / 1000)

                # save out trial level (2-s pupil epoch for real-time cumulative mean/std baselining)
                if raw_trial < 10:
                    f_prefix = '000'
                elif raw_trial >= 10 and raw_trial < 100:
                    f_prefix = '00'
                elif raw_trial >= 100:
                    f_prefix = '0'
                cur_pupils_pickle_filename = os.path.join(self.cur_pupil_pickle_dir, "2s-baseline_pupil_" + f_prefix + str(raw_trial) + '_' + os.path.basename(stim)[:-4] + '.pickle')
                pupils_np = np.asarray(pupils)
                with open(cur_pupils_pickle_filename, 'wb') as handle:
                    pickle.dump(pupils_np, handle, protocol=pickle.HIGHEST_PROTOCOL)
                
                cur_pupils_pickle_filename = os.path.join(self.cur_pupil_pickle_dir, "2s-baseline_ts_" + f_prefix + str(raw_trial) + '_' + os.path.basename(stim)[:-4] + '.pickle')
                pupils_ts_np = np.asarray(pupils_ts)
                with open(cur_pupils_pickle_filename, 'wb') as handle:
                    pickle.dump(pupils_ts_np, handle, protocol=pickle.HIGHEST_PROTOCOL)
                    
                ## store latest real-time pupil and corresponding timeseries
                self.LATEST_REALTIME_PUPIL = pupils_np
                self.LATEST_REALTIME_PUPIL_TS = pupils_ts_np
        
        # save out trial level (1000-ms pupil epoch) for fixation pre-stim at retrieval
        if phase == "ret" and is_post_ret_probe_fixation:
            # (1) epoch [0ms 1000ms]
            live_ret_p1_pupil_sampling_timer = core.CountdownTimer(self.post_trigger_p1_epoch_time)
            if self.eyetrack:
                while live_ret_p1_pupil_sampling_timer.getTime() >= 0:
                    cur_pupil, cur_time = self.GetPupilSize()
                    pupils_p1.append(cur_pupil)
                    pupils_p1_ts.append(cur_time)
                    time.sleep(1 / 1000)

            # (2) save out trial level p1 and p2 assays
            if trial < 10:
                f_prefix = '000'
            elif trial >= 10 and trial < 100:
                f_prefix = '00'
            elif trial >= 100:
                f_prefix = '0'
            
            ## save out the p1 assay
            ### pupil array
            cur_pupils_pickle_filename = os.path.join(self.cur_pupil_pickle_dir, "p1_pupil_" + f_prefix + str(trial) + '_' + os.path.basename(stim)[:-4] + '.pickle')
            pupils_p1_np = np.asarray(pupils_p1)
            with open(cur_pupils_pickle_filename, 'wb') as handle:
                pickle.dump(pupils_p1_np, handle, protocol=pickle.HIGHEST_PROTOCOL)
            
            ### pupil timestamps array
            cur_pupils_pickle_filename = os.path.join(self.cur_pupil_pickle_dir, "p1_ts_" + f_prefix + str(trial) + '_' + os.path.basename(stim)[:-4] + '.pickle')
            pupils_p1_ts_np = np.asarray(pupils_p1_ts)
            with open(cur_pupils_pickle_filename, 'wb') as handle:
                pickle.dump(pupils_p1_ts_np, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
        if phase == "prac-enc":
            core.wait(duration)
            
        if phase == "prac-ret":
            core.wait(7.31)
                        
        # if phase == "ret" and not is_post_ret_probe_fixation:
        #     core.wait(duration)
            
        if is_dud_trigger:
            core.wait(duration)

        if phase == "enc" and message_flag == "PRESTIM":
            core.wait(duration)

        if phase == "enc" and message_flag == "PREGOAL":
            core.wait(duration)
        
        offset = self.elapsed_run_clock.getTime()
            
        return onset, offset
    
    def _make_negative_to_positive_flicker(self, hold_time):
        fix_size = 36
        fixation = visual.TextStim(win=self.experiment_window, colorSpace='rgb255', font='Times', color=self.color_text, bold=False, text='+', height=fix_size, pos=[0,0])
        fixation.draw()
        circle_probe = visual.Circle(win=self.experiment_window, colorSpace='rgb255', fillColor=None, radius=75, units='pix', lineWidth=2, lineColor=self.color_text, opacity=0.3)
        circle_probe.draw()
        self.experiment_window.flip()
        core.wait(hold_time/2)
        fixation.draw()
        self.experiment_window.flip()
        core.wait(hold_time/2)
    
    def make_reorienting_probe(self, duration, stim=None, send_eyelink_message=False):
        n_flickers = int(duration / self.reorienting_flicker_rate)
        for n in range(0, n_flickers):
            if n == 0:
                onset = self.elapsed_run_clock.getTime()
                if self.eyetrack and send_eyelink_message:
                    stim_basename = os.path.basename(stim)
                    self.el_tracker.sendMessage('TRIG_S %s' % (stim_basename))
            self._make_negative_to_positive_flicker(self.reorienting_flicker_rate)
        offset = self.elapsed_run_clock.getTime()
        if self.eyetrack and send_eyelink_message:
            stim_basename = os.path.basename(stim)
            self.el_tracker.sendMessage('TRIG_E %s' % (stim_basename))
        
        return onset, offset
    
    def make_control_probe(self, stim=None, send_eyelink_message=False):
        # control circle probe
        # fillColor -- mean R/G/B luminance pooled values (on the 255 already SHINEd stims being used from Madore et al., 2020) calculated by the SHINE_color script (https://github.com/RodDalBen/SHINE_color)
        circle_probe = visual.Circle(win=self.experiment_window, colorSpace='rgb255', fillColor=(209, 204, 198), radius=self.ret_stim/2, units='pix')
        circle_probe.draw()
        self.experiment_window.flip()

        onset = self.elapsed_run_clock.getTime()
        
        if self.eyetrack and send_eyelink_message:
            stim_basename = os.path.basename(stim)
            self.el_tracker.sendMessage('CTRL_S %s' % (stim_basename))
        
        core.wait(random.choice([1.5, 1.75, 2, 2.25, 2.5]))
        
        offset = self.elapsed_run_clock.getTime()

        if self.eyetrack and send_eyelink_message:
            stim_basename = os.path.basename(stim)
            self.el_tracker.sendMessage('CTRL_E %s' % (stim_basename))
        
        return onset, offset
        
    def make_goal(self, duration, goal_type, phase=None, stim=None, send_eyelink_message=False):
        assert phase in ('enc', 'ret', 'prac-enc', 'prac-ret')

        if phase == "enc" or phase == "prac-enc":
            goal_mapping = {
                'PLUP' : self.enc_conceptual_goal,
                'BGSM' : self.enc_perceptual_goal,
            }
        elif phase == "ret" or phase == "prac-ret":
            goal_mapping = {
                'PLUP' : self.ret_conceptual_goal,
                'BGSM' : self.ret_perceptual_goal,
                'NOV' : self.ret_novel_goal,
            }

        cue = visual.TextStim(win=self.experiment_window, text=goal_mapping.get(goal_type), colorSpace='rgb255', font='Times', color=self.color_text, height=36, bold=False, wrapWidth=self.experiment_window.size[0])
        cue.draw()
        self.experiment_window.flip()
        onset = self.elapsed_run_clock.getTime()
        if self.eyetrack and send_eyelink_message:
            stim_basename = os.path.basename(stim)
            self.el_tracker.sendMessage('GOAL %s' % (stim_basename))
        core.wait(duration)
        offset = self.elapsed_run_clock.getTime()

        return onset, offset

    def make_probe(self, duration, size, enc_goal_state=None, resp=None, phase=None, stim=None, send_eyelink_message=False):
        if resp is None:
            if phase == "enc" or phase == "prac-enc":
                resp = self.response_keys_enc
            elif phase == "ret" or phase == "prac-ret":
                resp = self.response_keys_ret
            
        terminate_trials_on_keypress = False
        
        if phase == "ret" or phase == "prac-ret":
            terminate_trials_on_keypress = True

        trial_clock = core.Clock()

        response_acc = None
        ret_label = "NO_RESPONSE"

        if size == "SMALL":
            stim_size = self.enc_small_stim
        elif size == "BIG":
            stim_size = self.enc_big_stim
        else:
            stim_size = self.ret_stim

        probe_stim = visual.ImageStim(win=self.experiment_window, image=stim, size=stim_size, units='pix')
        probe_stim.autoDraw = True
        probe_stim.draw()
        self.experiment_window.flip()
        onset = self.elapsed_run_clock.getTime()
        if self.eyetrack and send_eyelink_message:
            stim_basename = os.path.basename(stim)
            self.el_tracker.sendMessage('PROBE_S %s' % (stim_basename))

        start_response = trial_clock.getTime()

        stop_listening = False
        response_timer = core.CountdownTimer(duration)

        while not stop_listening:
            # listen for keypresses
            keys = event.waitKeys(maxWait=duration, keyList=resp)

            # if no response was made after all the time elapses
            if response_timer.getTime() < 0 and keys is None:
                stop_listening = True
                response_key = None
                response_rt = None
                probe_stim.autoDraw = False
                offset = self.elapsed_run_clock.getTime()
            # if a 'Bigger/Smaller Before?' response was made (i.e., perceptual goal)
            elif resp[0] in keys:
                stop_listening = True
                response_key = resp[0]
                response_rt = trial_clock.getTime() - start_response
                if phase == "ret" or phase == "prac-ret":
                    ret_label = "BGSM"
                if not terminate_trials_on_keypress:
                    core.wait(response_timer.getTime())
                probe_stim.autoDraw = False
                offset = self.elapsed_run_clock.getTime()
            # if a 'Pleasant/Unpleasant Before?' response was made (i.e., conceptual goal)
            elif resp[1] in keys:
                stop_listening = True
                response_key = resp[1]
                response_rt = trial_clock.getTime() - start_response
                if phase == "ret" or phase == "prac-ret":
                    ret_label = "PLUP"
                if not terminate_trials_on_keypress:
                    core.wait(response_timer.getTime())
                probe_stim.autoDraw = False
                offset = self.elapsed_run_clock.getTime()
            # if an 'Old Item' but unsure of goal response was made
            elif resp[2] in keys:
                stop_listening = True
                response_key = resp[2]
                response_rt = trial_clock.getTime() - start_response
                if phase == "ret" or phase == "prac-ret":
                    ret_label = "OLD"
                if not terminate_trials_on_keypress:
                    core.wait(response_timer.getTime())
                probe_stim.autoDraw = False
                offset = self.elapsed_run_clock.getTime()
            # if a 'New Item' response was made (i.e., novel goal)
            elif resp[3] in keys:
                stop_listening = True
                response_key = resp[3]
                response_rt = trial_clock.getTime() - start_response
                if phase == "ret" or phase == "prac-ret":
                    ret_label = "NOV"
                if not terminate_trials_on_keypress:
                    core.wait(response_timer.getTime())
                probe_stim.autoDraw = False
                offset = self.elapsed_run_clock.getTime()
                
        if self.eyetrack and send_eyelink_message:
            stim_basename = os.path.basename(stim)
            self.el_tracker.sendMessage('PROBE_E %s' % (stim_basename))

        if phase == "enc" or phase == "prac-enc":
            ret_label = "NA"

        if phase == "enc" or phase == "prac-enc":
            if enc_goal_state == "BGSM" and response_key == resp[0] and size == "BIG":
                response_acc = 1
            elif enc_goal_state == "BGSM" and response_key == resp[0] and size == "SMALL":
                response_acc = 0
            elif enc_goal_state == "BGSM" and response_key == resp[1] and size == "BIG":
                response_acc = 0
            elif enc_goal_state == "BGSM" and response_key == resp[1] and size == "SMALL":
                response_acc = 1

        return response_key, response_rt, response_acc, ret_label, onset, offset

    """Stim set generation and validation
    """
    def build_task_stimset(self, save=True):
        if save:
            if not os.path.exists(os.path.join(self.experiment_info['Subject Number'], 'session')):
                os.makedirs(os.path.join(self.experiment_info['Subject Number'], 'session'))

        # shuffle stim pool
        stim_pool = random.sample(self.stim_pool, len(self.stim_pool))
        stim_pool = stim_pool[:self.n_stims_ret]

        # counterbalanced assignments of each goal state
        old_goals = (
                        (["PLUP_BIG_OLD"] * ((self.n_trials_per_run_enc // 4)) * self.n_runs_enc) +
                        (["PLUP_SMALL_OLD"] * ((self.n_trials_per_run_enc // 4)) * self.n_runs_enc) +
                        (["BGSM_BIG_OLD"] * ((self.n_trials_per_run_enc // 4)) * self.n_runs_enc) +
                        (["BGSM_SMALL_OLD"] * ((self.n_trials_per_run_enc // 4)) * self.n_runs_enc) +
                        (["NOV_REG_NEW"] * self.n_new_stims)
        )
        
        enc_blocks = ([1, 2, 3] * self.n_trials_per_run_enc) + ([-1] * (self.n_new_stims))
        ret_blocks = ([1, 2, 3] * self.n_trials_per_run_enc) + ([1, 2, 3] * (self.n_new_stims // 3))

        # stitch them together
        old_dict = { 'stim' : stim_pool, 'enc_goal' : old_goals, 'enc_block' : enc_blocks, 'ret_block' : ret_blocks }

        # turn them into dataframes
        old_df = pd.DataFrame(old_dict)

        # expand columns built above
        old_df[['enc_goal', 'enc_size', 'item_old_new']] = old_df.enc_goal.str.split("_", expand=True)

        # shuffle the stim set once
        old_df = old_df.sample(frac=1)

        # break global df into enc/ret specific subsets
        stims_enc1 = old_df[old_df['enc_block'] == 1]
        stims_enc2 = old_df[old_df['enc_block'] == 2]
        stims_enc3 = old_df[old_df['enc_block'] == 3]
        
        stims_ret1 = old_df[old_df['ret_block'] == 1]
        stims_ret2 = old_df[old_df['ret_block'] == 2]
        stims_ret3 = old_df[old_df['ret_block'] == 3]

        # validate the stim set (based on consecutive goal state occurances)
        stims_enc1 = run_enc_validation(stims_enc1)
        stims_enc2 = run_enc_validation(stims_enc2)
        stims_enc3 = run_enc_validation(stims_enc3)
        
        stims_ret1 = run_ret_validation(stims_ret1)
        stims_ret2 = run_ret_validation(stims_ret2)
        stims_ret3 = run_ret_validation(stims_ret3)
        
        # assert valid stim sets before saving out
        check_enc_stim_set(stims_enc1)
        check_enc_stim_set(stims_enc2)
        check_enc_stim_set(stims_enc3)

        check_ret_stim_set(stims_ret1)
        check_ret_stim_set(stims_ret2)
        check_ret_stim_set(stims_ret3)

        # save out generated stimlists
        stims_enc1_fname = self.validate_fname(os.path.join(self.experiment_info['Subject Number'], 'session', 'stimlist_enc1'))
        stims_enc2_fname = self.validate_fname(os.path.join(self.experiment_info['Subject Number'], 'session', 'stimlist_enc2'))
        stims_enc3_fname = self.validate_fname(os.path.join(self.experiment_info['Subject Number'], 'session', 'stimlist_enc3'))

        stims_ret1_fname = self.validate_fname(os.path.join(self.experiment_info['Subject Number'], 'session', 'stimlist_ret1'))
        stims_ret2_fname = self.validate_fname(os.path.join(self.experiment_info['Subject Number'], 'session', 'stimlist_ret2'))
        stims_ret3_fname = self.validate_fname(os.path.join(self.experiment_info['Subject Number'], 'session', 'stimlist_ret3'))

        stims_enc1.to_csv(stims_enc1_fname, index=False) if save else None
        stims_enc2.to_csv(stims_enc2_fname, index=False) if save else None
        stims_enc3.to_csv(stims_enc3_fname, index=False) if save else None

        stims_ret1.to_csv(stims_ret1_fname, index=False) if save else None
        stims_ret2.to_csv(stims_ret2_fname, index=False) if save else None
        stims_ret3.to_csv(stims_ret3_fname, index=False) if save else None

    def load_task_stimset(self):
        stims_enc1 = pd.read_csv(os.path.join(self.experiment_info['Subject Number'], 'session', 'stimlist_enc1.csv'))
        stims_enc2 = pd.read_csv(os.path.join(self.experiment_info['Subject Number'], 'session', 'stimlist_enc2.csv'))
        stims_enc3 = pd.read_csv(os.path.join(self.experiment_info['Subject Number'], 'session', 'stimlist_enc3.csv'))

        self.encoding_stim_list = pd.concat([stims_enc1,
                                             stims_enc2,
                                             stims_enc3])

        stims_ret1 = pd.read_csv(os.path.join(self.experiment_info['Subject Number'], 'session', 'stimlist_ret1.csv'))
        stims_ret2 = pd.read_csv(os.path.join(self.experiment_info['Subject Number'], 'session', 'stimlist_ret2.csv'))
        stims_ret3 = pd.read_csv(os.path.join(self.experiment_info['Subject Number'], 'session', 'stimlist_ret3.csv'))

        self.retrieval_stim_list = pd.concat([stims_ret1,
                                              stims_ret2,
                                              stims_ret3])

    """Task routine functions
    """
    def task_loop(self, phase, block):
        self.cur_pupil_pickle_dir = self.open_csv_data_file(phase, block)

        # reset trigger counts for probability distribution and pupil history at the beginning of each block
        self.trigger_true_count = 0
        self.trigger_false_count = 0
        self.trigger_true_current_pct = 0
        self.trigger_false_current_pct = 0
        self.NEXT_should_launch_real_trigger = None
        self.trigger_delivery_history = []
        self.LATEST_REALTIME_PUPIL = None
        self.LATEST_REALTIME_PUPIL_TS = None
        self.REALTIME_BLOCKWISE_PUPIL_MEANS = []
        self.REALTIME_BLOCKWISE_PUPIL_STDS = []

        latest_baseline_mean = None

        if phase == "enc":
            n_stims = self.n_trials_per_run_enc
            blockwise_stimset = self.encoding_stim_list[self.encoding_stim_list['enc_block'] == block]
            assert n_stims == len(blockwise_stimset), "Fatal assertion error: incorrect number of encoding stimuli for block... check stimuli files"
            self.real_task_run = True
        elif phase == "ret":
            n_stims = self.n_trials_per_run_ret
            blockwise_stimset = self.retrieval_stim_list[self.retrieval_stim_list['ret_block'] == block]
            assert n_stims == len(blockwise_stimset), "Fatal assertion error: incorrect number of retrieval stimuli for block... check stimuli files"
            self.real_task_run = True
            
        elif phase == "prac-enc":
            n_stims = len(self.enc_prac_stims)
            self.real_task_run = False
        elif phase == "prac-ret":
            n_stims = len(self.ret_prac_stims)
            self.real_task_run = False
            
        send_eyelink_triggers = False
        if self.eyetrack and self.real_task_run:
            send_eyelink_triggers = True
            self.trigger_eyelink(phase=phase, block=block)

        if self.real_task_run:
            self.make_message(self.msg_cont_task)
        
        self.elapsed_run_clock = core.MonotonicClock()

        i_trial = 0
        raw_trial = 0
        
        # dict to keep track of number of control probes per stimulus (during retrieval)
        ctrl_probes_count_dict = {}
        
        while i_trial < n_stims:
            data = []
            
            burn_in_trial = False
            abort_ret_probe = False
            blink_ctrl_circleprobe_onset = 0
            blink_ctrl_circleprobe_offset = 0
            
            if self.real_task_run:
                trial_stim = blockwise_stimset.iloc[i_trial]['stim']
                trial_item_old_new = blockwise_stimset.iloc[i_trial]['item_old_new']
                trial_enc_goal_state = blockwise_stimset.iloc[i_trial]['enc_goal']

            if phase == "enc":
                trial_pregoal_iti = self.enc_pregoal_iti
                trial_goal_state_dur = self.enc_goal
                trial_prestim_iti = self.enc_preprobe_iti
                trial_stim_dur = self.enc_probe
                trial_stim_size = blockwise_stimset.iloc[i_trial]['enc_size']
            elif phase == "ret":
                trial_pregoal_iti = None
                trial_goal_state_dur = None
                trial_prestim_iti = self.ret_preprobe_iti
                trial_stim_dur = self.ret_probe
                trial_stim_size = "REG"
                if raw_trial < 20:
                    burn_in_trial = True
            elif phase == "prac-enc":
                trial_pregoal_iti = self.enc_pregoal_iti
                trial_goal_state_dur = self.enc_goal
                trial_prestim_iti = self.enc_preprobe_iti
                trial_stim_dur = self.enc_probe
                trial_stim = self.enc_prac_stims[i_trial]
                trial_stim_size = self.enc_prac_stim_sizes[i_trial]
                trial_enc_goal_state = self.enc_prac_goal_states[i_trial]
                trial_item_old_new = "OLD"
            elif phase == "prac-ret":
                trial_pregoal_iti = None
                trial_goal_state_dur = None
                trial_prestim_iti = self.ret_preprobe_iti
                trial_stim_dur = self.ret_probe
                trial_stim_size = "REG"
                trial_stim = self.ret_prac_stims[i_trial]
                trial_enc_goal_state = self.enc_ret_prac_goal_states[i_trial]
                trial_item_old_new = self.ret_prac_item_old_new[i_trial]

            if send_eyelink_triggers:
                self.el_tracker.sendMessage('TRIALID %d' % i_trial)
                
            # goal state cue
            if phase == "enc" or phase == "prac-enc":
                trial_goal_state = trial_enc_goal_state
            elif phase == "ret" or phase == "prac-ret":
                trial_goal_state = None
                
            if phase == "enc" or phase == "prac-enc":
                # pre-goal ITI
                pregoal_iti_onset, pregoal_iti_offset = self.make_fixation(
                    duration = trial_pregoal_iti,
                    phase = phase,
                    trial = i_trial,
                    stim = trial_stim,
                    message_flag = "PREGOAL",
                    send_eyelink_message = send_eyelink_triggers
                )
                
                goal_onset, goal_offset = self.make_goal(
                    duration = trial_goal_state_dur,
                    goal_type = trial_goal_state,
                    phase = phase,
                    stim = trial_stim,
                    send_eyelink_message = send_eyelink_triggers
                )
                
            elif phase == "ret" or phase == "prac-ret":
                pregoal_iti_onset = 0
                pregoal_iti_offset = 0
                goal_onset = 0
                goal_offset = 0
                
            # pre-stim ITI
            prestim_iti_onset, prestim_iti_offset = self.make_fixation(
                duration = trial_prestim_iti,
                phase = phase,
                trial = i_trial,
                stim = trial_stim,
                message_flag = "PRESTIM",
                send_eyelink_message = send_eyelink_triggers,
                raw_trial = raw_trial
            )
            
            if phase == "prac-enc" or phase == "enc" or phase == "prac-ret" or burn_in_trial:
                window_mean = 0
                window_mean_two = 0
                launch_trigger = 0
                should_launch_real_trigger = 0
                trigger_recording_start = 0
                trigger_recording_start_two = 0
                trigger_recording_end = 0
                trigger_recording_end_two = 0
                trigger_recording_duration = 0
                trigger_recording_duration_two = 0
                trigger_probe_onset = 0
                trigger_probe_offset = 0
                trigger_probe_duration = 0
                null_trigger_fix_onset = 0
                null_trigger_fix_offset = 0
                null_trigger_fix_duration = 0
                post_trigger_period_fix_onset = 0
                post_trigger_period_fix_offset = 0
                activate_trigger_gate = False
                try_assay_again = False
                uninterpolated_window_mean = 0
                uninterpolated_window_mean_two = 0
            
            if phase == "ret":
                # real-time trigger recording window (fixation) -- [opportunities 1 and 2]
                window_mean, launch_trigger, should_launch_real_trigger, trigger_recording_start, trigger_recording_end, trigger_recording_duration, trigger_probe_onset, trigger_probe_offset, trigger_probe_duration, null_trigger_fix_onset, null_trigger_fix_offset, null_trigger_fix_duration, post_trigger_period_fix_onset, post_trigger_period_fix_offset, activate_trigger_gate, try_assay_again, window_mean_two, trigger_recording_start_two, trigger_recording_end_two, trigger_recording_duration_two, uninterpolated_window_mean, uninterpolated_window_mean_two = self.RealTimeTrigger(
                    trial = i_trial,
                    stim = trial_stim,
                    is_burn_in_trial = burn_in_trial
                )

                self.trigger_delivery_history.append(should_launch_real_trigger)

                # determine whether or not to deliver a control trial based on a blink on the second real-time recording window assay
                if window_mean_two == 'blink':
                    # set counter for each stimulus that requires a circle control probe
                    ctrl_probes_count_dict[os.path.basename(trial_stim)] = ctrl_probes_count_dict.get(os.path.basename(trial_stim), 0) + 1
                    
                    current_ctrl_probes_count = ctrl_probes_count_dict.get(os.path.basename(trial_stim))
                    
                    if current_ctrl_probes_count <= self.ctrl_probe_contig_limit:
                        blink_ctrl_circleprobe_onset, blink_ctrl_circleprobe_offset = self.make_control_probe(
                            stim = trial_stim,
                            send_eyelink_message = send_eyelink_triggers
                        )
                        
                        abort_ret_probe = True
                        
                        response_key = 'ctrl_probe_blink_' + str(current_ctrl_probes_count)
                        response_rt = 0
                        response_acc = 0
                        ret_label = 'ctrl_probe_blink_' + str(current_ctrl_probes_count)
                        stim_onset = 0
                        stim_offset = 0
                    else:
                        abort_ret_probe = False
                        
            if not abort_ret_probe:
                # stim cue x enc/ret decision
                response_key, response_rt, response_acc, ret_label, stim_onset, stim_offset = self.make_probe(
                    duration = trial_stim_dur,
                    size = trial_stim_size,
                    enc_goal_state = trial_enc_goal_state,
                    phase = phase,
                    stim = trial_stim,
                    send_eyelink_message = send_eyelink_triggers
                )
            
            if phase == "enc" or phase == "prac-enc":
                cur_resp_mapping = self.response_keys_enc
            elif phase == "ret" or phase == "prac-ret":
                cur_resp_mapping = self.response_keys_ret

            if phase == "ret" and burn_in_trial:
                self.compute_cumulative_threshold()
                latest_baseline_mean = self.REALTIME_BLOCKWISE_PUPIL_MEANS[-1]
                self.participant_baseline_mean = np.nanmean(self.REALTIME_BLOCKWISE_PUPIL_MEANS)
                self.participant_baseline_std = self.REALTIME_BLOCKWISE_PUPIL_STDS[-1]
                self.participant_threshold_lower_bound = self.participant_baseline_mean - (self.participant_baseline_std * self.sd_trigger_scale)
                self.participant_threshold_upper_bound = self.participant_baseline_mean + (self.participant_baseline_std * self.sd_trigger_scale)
            
            data.append({
                'subject_id' : self.experiment_info['Subject Number'],
                'session_start' : self.session_timestamp,
                'phase' : phase,
                'block' : block,
                'global_time_elapsed_secs' : self.elapsed_time_clock.getTime(),
                'global_trial_index' : self.trial_index,
                'raw_trial' : raw_trial,
                'actual_stimulus_index' : i_trial,
                'abort_ret_trial' : abort_ret_probe,
                'burn_in_trial' : burn_in_trial,
                'pregoal_iti_onset' : pregoal_iti_onset,
                'pregoal_iti_offset' : pregoal_iti_offset,
                'pregoal_iti_duration_secs' : pregoal_iti_offset - pregoal_iti_onset,
                'pregoal_iti_set_time' : trial_pregoal_iti,
                'goal_onset' : goal_onset,
                'goal_offset' : goal_offset,
                'goal_duration_secs' : goal_offset - goal_onset,
                'goal_set_time' : trial_goal_state_dur,
                'prestim_iti_onset' : prestim_iti_onset,
                'prestim_iti_offset' : prestim_iti_offset,
                'prestim_iti_duration_secs' : prestim_iti_offset - prestim_iti_onset,
                'prestim_iti_set_time' : trial_prestim_iti,
                'stim_onset' : stim_onset,
                'stim_offset' : stim_offset,
                'stim_duration_secs' : stim_offset - stim_onset,
                'stim_set_time' : trial_stim_dur,
                'stim_file' : os.path.basename(trial_stim),
                'stim_old_new' : trial_item_old_new,
                'stim_size' : trial_stim_size,
                'trigger_try_assay_again': try_assay_again,
                'trigger_recording_start_one' : trigger_recording_start,
                'trigger_recording_end_one' : trigger_recording_end,
                'trigger_recording_duration_one' : trigger_recording_duration,
                'trigger_recording_start_two' : trigger_recording_start_two,
                'trigger_recording_end_two' : trigger_recording_end_two,
                'trigger_recording_duration_two' : trigger_recording_duration_two,
                'trigger_window_mean_one' : window_mean,
                'trigger_uninterpolated_window_mean_one' : uninterpolated_window_mean,
                'trigger_window_mean_two' : window_mean_two,
                'trigger_uninterpolated_window_mean_two' : uninterpolated_window_mean_two,
                'latest_baseline_mean' : latest_baseline_mean,
                'trigger_baseline_mean' : self.participant_baseline_mean,
                'trigger_baseline_std' : self.participant_baseline_std,
                'trigger_threshold_std_scale_fct' : self.sd_trigger_scale,
                'trigger_lower_threshold' : self.participant_threshold_lower_bound,
                'trigger_upper_threshold' : self.participant_threshold_upper_bound,
                'trigger_should_launch' : launch_trigger,
                'trigger_actually_delivered' : should_launch_real_trigger,
                'trigger_gate_activated' : activate_trigger_gate,
                'trigger_probdist_true_count' : self.trigger_true_count,
                'trigger_probdist_false_count' : self.trigger_false_count,
                'trigger_probdist_true_pct' : self.trigger_true_current_pct,
                'trigger_probdist_false_pct' : self.trigger_false_current_pct,
                'trigger_probe_onset' : trigger_probe_onset,
                'trigger_probe_offset' : trigger_probe_offset,
                'trigger_probe_duration' : trigger_probe_duration,
                'null_trigger_fix_onset' : null_trigger_fix_onset,
                'null_trigger_fix_offset' : null_trigger_fix_offset,
                'null_trigger_fix_duration' : null_trigger_fix_duration,
                'post_trigger_period_fix_onset' : post_trigger_period_fix_onset,
                'post_trigger_period_fix_offset' : post_trigger_period_fix_offset,
                'post_trigger_period_fix_duration' : post_trigger_period_fix_offset - post_trigger_period_fix_onset,
                'blink_ctrl_circleprobe_onset' : blink_ctrl_circleprobe_onset,
                'blink_ctrl_circleprobe_offset' : blink_ctrl_circleprobe_offset,
                'blink_ctrl_circleprobe_duration' : blink_ctrl_circleprobe_offset - blink_ctrl_circleprobe_onset,
                'enc_goal' : trial_enc_goal_state,
                'response_mapping' : cur_resp_mapping,
                'response_key' : response_key,
                'response_rt' : response_rt,
                'enc_response_acc' : response_acc,
                'ret_label' : ret_label,
                'screen_width' : self.experiment_window.size[0],
                'screen_height' : self.experiment_window.size[1],
                'screen_hz' : self.screen_hz,
                'use_eyelink' : self.experiment_info['EyeLink'],
                'stimset_mode' : self.experiment_info['UES'],
                'counterbalance_id' : self.experiment_info['CB'],
                'experimenter' : self.experiment_info['Experimenter Initials'],
            })
            self.send_data(data)
            self.save_data_to_csv()
            self.trial_index += 1

            if self.eyetrack and self.real_task_run:
                stim_basename = str(os.path.basename(trial_stim))
                self.el_tracker.sendMessage('TRIAL_RESULT %s' % (stim_basename))
                end_of_trial_status_message = 'TRIAL %d/%d , RAW_TRIAL %d , RESP: %s' % (int(i_trial+1), int(n_stims), int(raw_trial+1), str(response_key))
                self.el_tracker.sendCommand("record_status_message '%s'" % end_of_trial_status_message)
                
            if not abort_ret_probe:
                i_trial += 1
                
            raw_trial += 1

        self._make_blank_fixation()

        if self.eyetrack and self.real_task_run:
            self.disconnect_eyelink()

    def practice_loop(self, phase):
        prac_block = 0
        requested_quit = False

        if phase == "enc":
            prac_phase = "prac-enc"
        elif phase == "ret":
            prac_phase = "prac-ret"

        while not requested_quit:
            prac_block += 1
            self.make_message(self.msg_cont_prac)
            self.task_loop(phase=prac_phase, block=prac_block)
            keys = self.make_message(self.msg_rerun_prac, key_list=['r', 'c'])
            requested_quit = False if 'r' in keys else True

    def compute_cumulative_threshold(self):
        # get real-time pupil values
        raw_trial_level_pupil = self.LATEST_REALTIME_PUPIL
        raw_trial_level_pupil_timeseries = self.LATEST_REALTIME_PUPIL_TS
        
        # real-time pupil preprocessing
        ## (1) mask out duplicate samples from trial level pupil array
        masked_trial_level_pupil = remove_duplicate_pupil_samples(raw_trial_level_pupil, raw_trial_level_pupil_timeseries)
        
        ## (2) interpolate NaNs
        interp_trial_level_pupil = self.InterpolateNaNs(masked_trial_level_pupil)
        
        ## (3) get trial level mean / std
        mean_pupil = np.mean(interp_trial_level_pupil)
        
        if np.isnan(mean_pupil):
            mean_pupil = np.nan
            
        ## (4) add mean / std to global pupil mean / std lists
        self.REALTIME_BLOCKWISE_PUPIL_MEANS.append(mean_pupil)
        self.REALTIME_BLOCKWISE_PUPIL_STDS.append(np.nanstd(self.REALTIME_BLOCKWISE_PUPIL_MEANS))
        
    def break_block(self):
        self.make_message(self.msg_break, key_list=['c'])
        
        self.make_message(self.msg_loading, key_list=None)
        
        core.wait(1)
        
        self.make_message("<<< loaded successfully >>>", key_list=['c'])

    def quit_experiment(self):
        self.make_message(message_string=self.msg_finish, key_list=['q'])
        self.experiment_window.close()

    """Main run function
    """
    def run(self):
        self.chdir()

        ok = self.get_experiment_info()
        if not ok:
            print("Experiment has ended.")
            sys.exit(1)

        self.make_subject_dir()

        if self.experiment_info['UES'] == 'no':
            self.build_task_stimset()
            self.load_task_stimset()
        elif self.experiment_info['UES'] == 'yes':
            self.load_task_stimset()

        self.response_keys_enc = self.response_key_mappings.get('ps5e')
        self.response_keys_ret = self.response_key_mappings.get('ps5r')

        self.eyetrack = True if self.experiment_info['EyeLink'] == 'on' else False

        self.open_window(screen=0)
        self.screen_hz = self.experiment_window.getActualFrameRate(nIdentical=10, nMaxFrames=100, nWarmUpFrames=10, threshold=1)
        self.experiment_window.mouseVisible = False

        entry_point = self.experiment_info['EP']

        if not self.elapsed_time_clock:
            self.elapsed_time_clock = core.MonotonicClock()

        """Variable entry points logic
        """
        if entry_point == 'pp':
            self.PostProcConvertTrialLevelPickles()
        elif entry_point == 'r3':
            self.break_block()
            self.task_loop(phase="ret", block=3)
            self.PostProcConvertTrialLevelPickles()
        elif entry_point == 'e3':
            self.break_block()
            self.task_loop(phase="enc", block=3)
            self.break_block()
            self.task_loop(phase="ret", block=3)
            self.PostProcConvertTrialLevelPickles()
        elif entry_point == 'r2':
            self.break_block()
            self.task_loop(phase="ret", block=2)
            self.break_block()
            self.task_loop(phase="enc", block=3)
            self.break_block()
            self.task_loop(phase="ret", block=3)
            self.PostProcConvertTrialLevelPickles()
        elif entry_point == 'e2':
            self.break_block()
            self.task_loop(phase="enc", block=2)
            self.break_block()
            self.task_loop(phase="ret", block=2)
            self.break_block()
            self.task_loop(phase="enc", block=3)
            self.break_block()
            self.task_loop(phase="ret", block=3)
            self.PostProcConvertTrialLevelPickles()
        elif entry_point == 'r1':
            self.break_block()
            self.task_loop(phase="ret", block=1)
            self.break_block()
            self.task_loop(phase="enc", block=2)
            self.break_block()
            self.task_loop(phase="ret", block=2)
            self.break_block()
            self.task_loop(phase="enc", block=3)
            self.break_block()
            self.task_loop(phase="ret", block=3)
            self.PostProcConvertTrialLevelPickles()
        elif entry_point == 'e1':
            self.task_loop(phase="enc", block=1)
            self.break_block()
            self.task_loop(phase="ret", block=1)
            self.break_block()
            self.task_loop(phase="enc", block=2)
            self.break_block()
            self.task_loop(phase="ret", block=2)
            self.break_block()
            self.task_loop(phase="enc", block=3)
            self.break_block()
            self.task_loop(phase="ret", block=3)
            self.PostProcConvertTrialLevelPickles()
        elif entry_point == 'rp':
            self.practice_loop(phase="ret")
            self.task_loop(phase="enc", block=1)
            self.break_block()
            self.task_loop(phase="ret", block=1)
            self.break_block()
            self.task_loop(phase="enc", block=2)
            self.break_block()
            self.task_loop(phase="ret", block=2)
            self.break_block()
            self.task_loop(phase="enc", block=3)
            self.break_block()
            self.task_loop(phase="ret", block=3)
            self.PostProcConvertTrialLevelPickles()
        elif entry_point == 'ep':
            self.practice_loop(phase="enc")
            self.practice_loop(phase="ret")
            self.task_loop(phase="enc", block=1)
            self.break_block()
            self.task_loop(phase="ret", block=1)
            self.break_block()
            self.task_loop(phase="enc", block=2)
            self.break_block()
            self.task_loop(phase="ret", block=2)
            self.break_block()
            self.task_loop(phase="enc", block=3)
            self.break_block()
            self.task_loop(phase="ret", block=3)
            self.PostProcConvertTrialLevelPickles()

        self.quit_experiment()

"""Initiate and run experiment
"""
if __name__ == '__main__':
    exp = EpisodicClosedLoop(
        experiment_name = settings.EXPERIMENT_NAME,
        stim_directory = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), settings.STIM_DIRECTORY)),
        data_directory = os.path.join(os.path.expanduser('~'), 'Desktop', settings.EXPERIMENT_NAME, settings.DATA_DIRECTORY)
    )

    exp.run()
