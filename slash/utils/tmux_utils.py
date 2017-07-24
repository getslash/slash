import sys
import os
import libtmux
import logbook
from ..exceptions import TmuxSessionNotExist, TmuxExecutableNotFound
from ..ctx import context

DEFAULT_SESSION_NAME = 'slash_session'
TMUX_EXECUTABLE_NAME = 'tmux'
MASTER_WINDOW_NAME = 'master'

_logger = logbook.Logger(__name__)

def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

def is_in_tmux():
    return os.environ.get('TMUX') is not None

def get_slash_tmux_session(session_name):
    try:
        tmux_server = libtmux.Server()
        return tmux_server.find_where({"session_name":session_name})
    except libtmux.exc.LibTmuxException:
        _logger.debug('No tmux server is running')
        return

def create_new_window(window_name, command):
    slash_session = get_slash_tmux_session(context.session.id)
    if not slash_session:
        raise TmuxSessionNotExist("Slash tmux session not found, can't create new window")
    return slash_session.new_window(attach=False, window_name=window_name, window_shell=command)

def create_new_pane(command):
    slash_session = get_slash_tmux_session(context.session.id)
    if not slash_session:
        raise TmuxSessionNotExist("Slash tmux session not found, can't create new window")
    new_pane = slash_session.attached_window.split_window(attach=False)
    new_pane.send_keys(command)
    return new_pane

def run_slash_in_tmux(command):
    tmux_session = get_slash_tmux_session(DEFAULT_SESSION_NAME)
    if tmux_session:
        tmux_session.set_option('remain-on-exit', True)
        libtmux.Server().switch_client(DEFAULT_SESSION_NAME)
        tmux_session.rename_session(context.session.id)
    else:
        path_to_tmux = which(TMUX_EXECUTABLE_NAME)
        if not path_to_tmux:
            _logger.error("Tmux executable not found")
            raise TmuxExecutableNotFound("Tmux executable not found")
        command = ' '.join([sys.executable, '-m', 'slash.frontend.main', 'run'] + command)
        tmux_args = [path_to_tmux, 'new-session', '-s', DEFAULT_SESSION_NAME, '-n', MASTER_WINDOW_NAME]
        if is_in_tmux():
            tmux_args.append('-Ad')
        tmux_args.append(command)
        os.execve(path_to_tmux, tmux_args, dict(os.environ))
