#!/usr/bin/env python

r"""
This module provides command execution functions such as cmd_fnc and cmd_fnc_u.
"""

import os
import sys
import subprocess
import collections
import signal
import time
import re
import inspect

import gen_print as gp
import gen_valid as gv
import gen_misc as gm
import func_args as fa

robot_env = gp.robot_env

if robot_env:
    from robot.libraries.BuiltIn import BuiltIn


# cmd_fnc and cmd_fnc_u should now be considered deprecated.  shell_cmd and
# t_shell_cmd should be used instead.
def cmd_fnc(cmd_buf,
            quiet=None,
            test_mode=None,
            debug=0,
            print_output=1,
            show_err=1,
            return_stderr=0,
            ignore_err=1):
    r"""
    Run the given command in a shell and return the shell return code and the
    output.

    Description of arguments:
    cmd_buf                         The command string to be run in a shell.
    quiet                           Indicates whether this function should run
                                    the print_issuing() function which prints
                                    "Issuing: <cmd string>" to stdout.
    test_mode                       If test_mode is set, this function will
                                    not actually run the command.  If
                                    print_output is set, it will print
                                    "(test_mode) Issuing: <cmd string>" to
                                    stdout.
    debug                           If debug is set, this function will print
                                    extra debug info.
    print_output                    If this is set, this function will print
                                    the stdout/stderr generated by the shell
                                    command.
    show_err                        If show_err is set, this function will
                                    print a standardized error report if the
                                    shell command returns non-zero.
    return_stderr                   If return_stderr is set, this function
                                    will process the stdout and stderr streams
                                    from the shell command separately.  It
                                    will also return stderr in addition to the
                                    return code and the stdout.
    """

    # Determine default values.
    quiet = int(gm.global_default(quiet, 0))
    test_mode = int(gm.global_default(test_mode, 0))

    if debug:
        gp.print_vars(cmd_buf, quiet, test_mode, debug)

    err_msg = gv.valid_value(cmd_buf)
    if err_msg != "":
        raise ValueError(err_msg)

    if not quiet:
        gp.pissuing(cmd_buf, test_mode)

    if test_mode:
        if return_stderr:
            return 0, "", ""
        else:
            return 0, ""

    if return_stderr:
        err_buf = ""
        stderr = subprocess.PIPE
    else:
        stderr = subprocess.STDOUT

    sub_proc = subprocess.Popen(cmd_buf,
                                bufsize=1,
                                shell=True,
                                executable='/bin/bash',
                                stdout=subprocess.PIPE,
                                stderr=stderr)
    out_buf = ""
    if return_stderr:
        for line in sub_proc.stderr:
            try:
                err_buf += line
            except TypeError:
                line = line.decode("utf-8")
                err_buf += line
            if not print_output:
                continue
            gp.gp_print(line)
    for line in sub_proc.stdout:
        try:
            out_buf += line
        except TypeError:
            line = line.decode("utf-8")
            out_buf += line
        if not print_output:
            continue
        gp.gp_print(line)
    if print_output and not robot_env:
        sys.stdout.flush()
    sub_proc.communicate()
    shell_rc = sub_proc.returncode
    if shell_rc != 0:
        err_msg = "The prior shell command failed.\n"
        err_msg += gp.sprint_var(shell_rc, gp.hexa())
        if not print_output:
            err_msg += "out_buf:\n" + out_buf

        if show_err:
            gp.print_error_report(err_msg)
        if not ignore_err:
            if robot_env:
                BuiltIn().fail(err_msg)
            else:
                raise ValueError(err_msg)

    if return_stderr:
        return shell_rc, out_buf, err_buf
    else:
        return shell_rc, out_buf


def cmd_fnc_u(cmd_buf,
              quiet=None,
              debug=None,
              print_output=1,
              show_err=1,
              return_stderr=0,
              ignore_err=1):
    r"""
    Call cmd_fnc with test_mode=0.  See cmd_fnc (above) for details.

    Note the "u" in "cmd_fnc_u" stands for "unconditional".
    """

    return cmd_fnc(cmd_buf, test_mode=0, quiet=quiet, debug=debug,
                   print_output=print_output, show_err=show_err,
                   return_stderr=return_stderr, ignore_err=ignore_err)


def parse_command_string(command_string):
    r"""
    Parse a bash command-line command string and return the result as a
    dictionary of parms.

    This can be useful for answering questions like "What did the user specify
    as the value for parm x in the command string?".

    This function expects the command string to follow the following posix
    conventions:
    - Short parameters:
      -<parm name><space><arg value>
    - Long parameters:
      --<parm name>=<arg value>

    The first item in the string will be considered to be the command.  All
    values not conforming to the specifications above will be considered
    positional parms.  If there are multiple parms with the same name, they
    will be put into a list (see illustration below where "-v" is specified
    multiple times).

    Description of argument(s):
    command_string                  The complete command string including all
                                    parameters and arguments.

    Sample input:

    robot_cmd_buf:                                    robot -v
    OPENBMC_HOST:dummy1 -v keyword_string:'Set Auto Reboot  no' -v
    lib_file_path:/home/user1/git/openbmc-test-automation/lib/utils.robot -v
    quiet:0 -v test_mode:0 -v debug:0
    --outputdir='/home/user1/status/children/'
    --output=dummy1.Auto_reboot.170802.124544.output.xml
    --log=dummy1.Auto_reboot.170802.124544.log.html
    --report=dummy1.Auto_reboot.170802.124544.report.html
    /home/user1/git/openbmc-test-automation/extended/run_keyword.robot

    Sample output:

    robot_cmd_buf_dict:
      robot_cmd_buf_dict[command]:                    robot
      robot_cmd_buf_dict[v]:
        robot_cmd_buf_dict[v][0]:                     OPENBMC_HOST:dummy1
        robot_cmd_buf_dict[v][1]:                     keyword_string:Set Auto
        Reboot no
        robot_cmd_buf_dict[v][2]:
        lib_file_path:/home/user1/git/openbmc-test-automation/lib/utils.robot
        robot_cmd_buf_dict[v][3]:                     quiet:0
        robot_cmd_buf_dict[v][4]:                     test_mode:0
        robot_cmd_buf_dict[v][5]:                     debug:0
      robot_cmd_buf_dict[outputdir]:
      /home/user1/status/children/
      robot_cmd_buf_dict[output]:
      dummy1.Auto_reboot.170802.124544.output.xml
      robot_cmd_buf_dict[log]:
      dummy1.Auto_reboot.170802.124544.log.html
      robot_cmd_buf_dict[report]:
      dummy1.Auto_reboot.170802.124544.report.html
      robot_cmd_buf_dict[positional]:
      /home/user1/git/openbmc-test-automation/extended/run_keyword.robot
    """

    # We want the parms in the string broken down the way bash would do it,
    # so we'll call upon bash to do that by creating a simple inline bash
    # function.
    bash_func_def = "function parse { for parm in \"${@}\" ; do" +\
        " echo $parm ; done ; }"

    rc, outbuf = cmd_fnc_u(bash_func_def + " ; parse " + command_string,
                           quiet=1, print_output=0)
    command_string_list = outbuf.rstrip("\n").split("\n")

    command_string_dict = collections.OrderedDict()
    ix = 1
    command_string_dict['command'] = command_string_list[0]
    while ix < len(command_string_list):
        if command_string_list[ix].startswith("--"):
            key, value = command_string_list[ix].split("=")
            key = key.lstrip("-")
        elif command_string_list[ix].startswith("-"):
            key = command_string_list[ix].lstrip("-")
            ix += 1
            try:
                value = command_string_list[ix]
            except IndexError:
                value = ""
        else:
            key = 'positional'
            value = command_string_list[ix]
        if key in command_string_dict:
            if isinstance(command_string_dict[key], str):
                command_string_dict[key] = [command_string_dict[key]]
            command_string_dict[key].append(value)
        else:
            command_string_dict[key] = value
        ix += 1

    return command_string_dict


# Save the original SIGALRM handler for later restoration by shell_cmd.
original_sigalrm_handler = signal.getsignal(signal.SIGALRM)


def shell_cmd_timed_out(signal_number,
                        frame):
    r"""
    Handle an alarm signal generated during the shell_cmd function.
    """

    gp.dprint_executing()
    global command_timed_out
    command_timed_out = True
    # Get subprocess pid from shell_cmd's call stack.
    sub_proc = gp.get_stack_var('sub_proc', 0)
    pid = sub_proc.pid
    gp.dprint_var(pid)
    # Terminate the child process group.
    os.killpg(pid, signal.SIGKILL)
    # Restore the original SIGALRM handler.
    signal.signal(signal.SIGALRM, original_sigalrm_handler)

    return


def shell_cmd(command_string,
              quiet=None,
              print_output=None,
              show_err=1,
              test_mode=0,
              time_out=None,
              max_attempts=1,
              retry_sleep_time=5,
              valid_rcs=[0],
              ignore_err=None,
              return_stderr=0,
              fork=0):
    r"""
    Run the given command string in a shell and return a tuple consisting of
    the shell return code and the output.

    Description of argument(s):
    command_string                  The command string to be run in a shell
                                    (e.g. "ls /tmp").
    quiet                           If set to 0, this function will print
                                    "Issuing: <cmd string>" to stdout.  When
                                    the quiet argument is set to None, this
                                    function will assign a default value by
                                    searching upward in the stack for the
                                    quiet variable value.  If no such value is
                                    found, quiet is set to 0.
    print_output                    If this is set, this function will print
                                    the stdout/stderr generated by the shell
                                    command to stdout.
    show_err                        If show_err is set, this function will
                                    print a standardized error report if the
                                    shell command fails (i.e. if the shell
                                    command returns a shell_rc that is not in
                                    valid_rcs).  Note: Error text is only
                                    printed if ALL attempts to run the
                                    command_string fail.  In other words, if
                                    the command execution is ultimately
                                    successful, initial failures are hidden.
    test_mode                       If test_mode is set, this function will
                                    not actually run the command.  If
                                    print_output is also set, this function
                                    will print "(test_mode) Issuing: <cmd
                                    string>" to stdout.  A caller should call
                                    shell_cmd directly if they wish to have
                                    the command string run unconditionally.
                                    They should call the t_shell_cmd wrapper
                                    (defined below) if they wish to run the
                                    command string only if the prevailing
                                    test_mode variable is set to 0.
    time_out                        A time-out value expressed in seconds.  If
                                    the command string has not finished
                                    executing within <time_out> seconds, it
                                    will be halted and counted as an error.
    max_attempts                    The max number of attempts that should be
                                    made to run the command string.
    retry_sleep_time                The number of seconds to sleep between
                                    attempts.
    valid_rcs                       A list of integers indicating which
                                    shell_rc values are not to be considered
                                    errors.
    ignore_err                      Ignore error means that a failure
                                    encountered by running the command string
                                    will not be raised as a python exception.
                                    When the ignore_err argument is set to
                                    None, this function will assign a default
                                    value by searching upward in the stack for
                                    the ignore_err variable value.  If no such
                                    value is found, ignore_err is set to 1.
    return_stderr                   If return_stderr is set, this function
                                    will process the stdout and stderr streams
                                    from the shell command separately.  In
                                    such a case, the tuple returned by this
                                    function will consist of three values
                                    rather than just two: rc, stdout, stderr.
    fork                            Run the command string asynchronously
                                    (i.e. don't wait for status of the child
                                    process and don't try to get
                                    stdout/stderr).
    """

    err_msg = gv.valid_value(command_string)
    if err_msg:
        raise ValueError(err_msg)

    # Assign default values to some of the arguments to this function.
    quiet = int(gm.dft(quiet, gp.get_stack_var('quiet', 0)))
    print_output = int(gm.dft(print_output, not quiet))
    show_err = int(show_err)
    ignore_err = int(gm.dft(ignore_err, gp.get_stack_var('ignore_err', 1)))

    gp.qprint_issuing(command_string, test_mode)
    if test_mode:
        return (0, "", "") if return_stderr else (0, "")

    # Convert a string python dictionary definition to a dictionary.
    valid_rcs = fa.source_to_object(valid_rcs)
    # Convert each list entry to a signed value.
    valid_rcs = [gm.to_signed(x) for x in valid_rcs]

    stderr = subprocess.PIPE if return_stderr else subprocess.STDOUT

    # Write all output to func_out_history_buf rather than directly to
    # stdout.  This allows us to decide what to print after all attempts to
    # run the command string have been made.  func_out_history_buf will
    # contain the complete history from the current invocation of this
    # function.
    global command_timed_out
    command_timed_out = False
    func_out_history_buf = ""
    for attempt_num in range(1, max_attempts + 1):
        sub_proc = subprocess.Popen(command_string,
                                    preexec_fn=os.setsid,
                                    bufsize=1,
                                    shell=True,
                                    universal_newlines=True,
                                    executable='/bin/bash',
                                    stdout=subprocess.PIPE,
                                    stderr=stderr)
        if fork:
            return (0, "", "") if return_stderr else (0, "")

        if time_out:
            command_timed_out = False
            # Designate a SIGALRM handling function and set alarm.
            signal.signal(signal.SIGALRM, shell_cmd_timed_out)
            signal.alarm(time_out)
        try:
            stdout_buf, stderr_buf = sub_proc.communicate()
        except IOError:
            command_timed_out = True
        # Restore the original SIGALRM handler and clear the alarm.
        signal.signal(signal.SIGALRM, original_sigalrm_handler)
        signal.alarm(0)

        # Output from this loop iteration is written to func_out_buf for
        # later processing.  This can include stdout, stderr and our own error
        # messages.
        func_out_buf = ""
        if print_output:
            if return_stderr:
                func_out_buf += stderr_buf
            func_out_buf += stdout_buf
        shell_rc = sub_proc.returncode
        if shell_rc in valid_rcs:
            break
        err_msg = "The prior shell command failed.\n"
        err_msg += gp.sprint_var(attempt_num)
        err_msg += gp.sprint_vars(command_string, command_timed_out, time_out)
        err_msg += gp.sprint_varx("child_pid", sub_proc.pid)
        err_msg += gp.sprint_vars(shell_rc, valid_rcs, fmt=gp.hexa())
        if not print_output:
            if return_stderr:
                err_msg += "stderr_buf:\n" + stderr_buf
            err_msg += "stdout_buf:\n" + stdout_buf
        if show_err:
            func_out_buf += gp.sprint_error_report(err_msg)
        if attempt_num < max_attempts:
            cmd_buf = "time.sleep(" + str(retry_sleep_time) + ")"
            if show_err:
                func_out_buf += gp.sprint_issuing(cmd_buf)
            exec(cmd_buf)
        func_out_history_buf += func_out_buf

    if shell_rc in valid_rcs:
        gp.gp_print(func_out_buf)
    else:
        if show_err:
            gp.gp_print(func_out_history_buf, stream='stderr')
        else:
            # There is no error information to show so just print output from
            # last loop iteration.
            gp.gp_print(func_out_buf)
        if not ignore_err:
            # If the caller has already asked to show error info, avoid
            # repeating that in the failure message.
            err_msg = "The prior shell command failed.\n" if show_err \
                else err_msg
            if robot_env:
                BuiltIn().fail(err_msg)
            else:
                raise ValueError(err_msg)

    return (shell_rc, stdout_buf, stderr_buf) if return_stderr \
        else (shell_rc, stdout_buf)


def t_shell_cmd(command_string, **kwargs):
    r"""
    Search upward in the the call stack to obtain the test_mode argument, add
    it to kwargs and then call shell_cmd and return the result.

    See shell_cmd prolog for details on all arguments.
    """

    if 'test_mode' in kwargs:
        error_message = "Programmer error - test_mode is not a valid" +\
            " argument to this function."
        gp.print_error_report(error_message)
        exit(1)

    test_mode = int(gp.get_stack_var('test_mode', 0))
    kwargs['test_mode'] = test_mode

    return shell_cmd(command_string, **kwargs)


def re_order_kwargs(stack_frame_ix, **kwargs):
    r"""
    Re-order the kwargs to match the order in which they were specified on a
    function invocation and return as an ordered dictionary.

    Note that this re_order_kwargs function should not be necessary in python
    versions 3.6 and beyond.

    Example:

    The caller calls func1 like this:

    func1('mike', arg1='one', arg2='two', arg3='three')

    And func1 is defined as follows:

    def func1(first_arg, **kwargs):

        kwargs = re_order_kwargs(first_arg_num=2, stack_frame_ix=3, **kwargs)

    The kwargs dictionary before calling re_order_kwargs (where order is not
    guaranteed):

    kwargs:
      kwargs[arg3]:          three
      kwargs[arg2]:          two
      kwargs[arg1]:          one

    The kwargs dictionary after calling re_order_kwargs:

    kwargs:
      kwargs[arg1]:          one
      kwargs[arg2]:          two
      kwargs[arg3]:          three

    Note that the re-ordered kwargs match the order specified on the call to
    func1.

    Description of argument(s):
    stack_frame_ix                  The stack frame of the function whose
                                    kwargs values must be re-ordered.  0 is
                                    the stack frame of re_order_kwargs, 1 is
                                    the stack from of its caller and so on.
    kwargs                          The keyword argument dictionary which is
                                    to be re-ordered.
    """

    new_kwargs = collections.OrderedDict()

    # Get position number of first keyword on the calling line of code.
    (args, varargs, keywords, locals) =\
        inspect.getargvalues(inspect.stack()[stack_frame_ix][0])
    first_kwarg_pos = 1 + len(args)
    if varargs is not None:
        first_kwarg_pos += len(locals[varargs])
    for arg_num in range(first_kwarg_pos, first_kwarg_pos + len(kwargs)):
        # This will result in an arg_name value such as "arg1='one'".
        arg_name = gp.get_arg_name(None, arg_num, stack_frame_ix + 2)
        # Continuing with the prior example, the following line will result
        # in key being set to 'arg1'.
        key = arg_name.split('=')[0]
        new_kwargs[key] = kwargs[key]

    return new_kwargs


def default_arg_delim(arg_dashes):
    r"""
    Return the default argument delimiter value for the given arg_dashes value.

    Note: this function is useful for functions that manipulate bash command
    line arguments (e.g. --parm=1 or -parm 1).

    Description of argument(s):
    arg_dashes                      The argument dashes specifier (usually,
                                    "-" or "--").
    """

    if arg_dashes == "--":
        return "="

    return " "


def create_command_string(command, *pos_parms, **options):
    r"""
    Create and return a bash command string consisting of the given arguments
    formatted as text.

    The default formatting of options is as follows:

    <single dash><option name><space delim><option value>

    Example:

    -parm value

    The caller can change the kind of dashes/delimiters used by specifying
    "arg_dashes" and/or "arg_delims" as options.  These options are processed
    specially by the create_command_string function and do NOT get inserted
    into the resulting command string.  All options following the
    arg_dashes/arg_delims options will then use the specified values for
    dashes/delims.  In the special case of arg_dashes equal to "--", the
    arg_delim will automatically be changed to "=".  See examples below.

    Quoting rules:

    The create_command_string function will single quote option values as
    needed to prevent bash expansion.  If the caller wishes to defeat this
    action, they may single or double quote the option value themselves.  See
    examples below.

    pos_parms are NOT automatically quoted.  The caller is advised to either
    explicitly add quotes or to use the quote_bash_parm functions to quote any
    pos_parms.

    Examples:

    command_string = create_command_string('cd', '~')

    Result:
    cd ~

    Note that the pos_parm ("~") does NOT get quoted, as per the
    aforementioned rules.  If quotes are desired, they may be added explicitly
    by the caller:

    command_string = create_command_string('cd', '\'~\'')

    Result:
    cd '~'

    command_string = create_command_string('grep', '\'^[^ ]*=\'',
        '/tmp/myfile', i=None, m='1', arg_dashes='--', color='always')

    Result:
    grep -i -m 1 --color=always '^[^ ]*=' /tmp/myfile

    In the preceding example, note the use of None to cause the "i" parm to be
    treated as a flag (i.e. no argument value is generated).  Also, note the
    use of arg_dashes to change the type of dashes used on all subsequent
    options.  The following example is equivalent to the prior.  Note that
    quote_bash_parm is used instead of including the quotes explicitly.

    command_string = create_command_string('grep', quote_bash_parm('^[^ ]*='),
        '/tmp/myfile', i=None,  m='1', arg_dashes='--', color='always')

    Result:
    grep -i -m 1 --color=always '^[^ ]*=' /tmp/myfile

    In the following example, note the automatic quoting of the password
    option, as per the aforementioned rules.

    command_string = create_command_string('my_pgm', '/tmp/myfile', i=None,
        m='1', arg_dashes='--', password='${my_pw}')

    However, let's say that the caller wishes to have bash expand the password
    value.  To achieve this, the caller can use double quotes:

    command_string = create_command_string('my_pgm', '/tmp/myfile', i=None,
        m='1', arg_dashes='--', password='"${my_pw}"')

    Result:
    my_pgm -i -m 1 --password="${my_pw}" /tmp/myfile

    command_string = create_command_string('ipmitool', 'power status',
        I='lanplus', C='3', U='root', P='0penBmc', H='wsbmc010')

    Result:
    ipmitool -I lanplus -C 3 -U root -P 0penBmc -H wsbmc010 power status

    By default create_command_string will take measures to preserve the order
    of the callers options.  In some cases, this effort may fail (as when
    calling directly from a robot program).  In this case, the caller can
    accept the responsibility of keeping an ordered list of options by calling
    this function with the last positional parm as some kind of dictionary
    (preferably an OrderedDict) and avoiding the use of any actual option args.

    Example:
    kwargs = collections.OrderedDict([('pass', 0), ('fail', 0)])
    command_string = create_command_string('my program', 'pos_parm1', kwargs)

    Result:

    my program -pass 0 -fail 0 pos_parm1

    Note to programmers who wish to write a wrapper to this function:  If the
    python version is less than 3.6, to get the options to be processed
    correctly, the wrapper function must include a _stack_frame_ix_ keyword
    argument to allow this function to properly re-order options:

    def create_ipmi_ext_command_string(command, **kwargs):

        return create_command_string('ipmitool', command, _stack_frame_ix_=2,
            **kwargs)

    Example call of wrapper function:

    command_string = create_ipmi_ext_command_string('power status',
    I='lanplus')

    Description of argument(s):
    command                         The command (e.g. "cat", "sort",
                                    "ipmitool", etc.).
    pos_parms                       The positional parms for the command (e.g.
                                    PATTERN, FILENAME, etc.).  These will be
                                    placed at the end of the resulting command
                                    string.
    options                         The command options (e.g. "-m 1",
                                    "--max-count=NUM", etc.).  Note that if
                                    the value of any option is None, then it
                                    will be understood to be a flag (for which
                                    no value is required).
    """

    arg_dashes = "-"
    delim = default_arg_delim(arg_dashes)

    command_string = command

    if len(pos_parms) > 0 and gp.is_dict(pos_parms[-1]):
        # Convert pos_parms from tuple to list.
        pos_parms = list(pos_parms)
        # Re-assign options to be the last pos_parm value (which is a
        # dictionary).
        options = pos_parms[-1]
        # Now delete the last pos_parm.
        del pos_parms[-1]
    else:
        # Either get stack_frame_ix from the caller via options or set it to
        # the default value.
        stack_frame_ix = options.pop('_stack_frame_ix_', 1)
        if gm.python_version < gm.ordered_dict_version:
            # Re-establish the original options order as specified on the
            # original line of code.  This function depends on correct order.
            options = re_order_kwargs(stack_frame_ix, **options)
    for key, value in options.items():
        # Check for special values in options and process them.
        if key == "arg_dashes":
            arg_dashes = str(value)
            delim = default_arg_delim(arg_dashes)
            continue
        if key == "arg_delim":
            delim = str(value)
            continue
        # Format the options elements into the command string.
        command_string += " " + arg_dashes + key
        if value is not None:
            command_string += delim
            if re.match(r'^(["].*["]|[\'].*[\'])$', str(value)):
                # Already quoted.
                command_string += str(value)
            else:
                command_string += gm.quote_bash_parm(str(value))
    # Finally, append the pos_parms to the end of the command_string.  Use
    # filter to eliminate blank pos parms.
    command_string = ' '.join([command_string] + list(filter(None, pos_parms)))

    return command_string
