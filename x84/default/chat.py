""" Chat script for x/84, https://github.com/jquast/x84 """

# unfortunately the hardlinemode stuff that irssi and such uses
# is not used, so each line causes a full screen fresh ..

import time
POLL_KEY = 0.05 # blocking ;; how often to poll keyboard
POLL_OUT = 0.25 # seconds elapsed before screen update, prevents flood


CHANNEL = None
NICKS = dict()

def show_help():
    return u'\n'.join((
        u'   /join #channel',
        u'   /act mesg',
        u'   /part [reason]',
        u'   /quit [reason]',
        u'   /users',
        u'   /whois handle',))

def process(mesg):
    from x84.bbs import getsession
    session = getsession()
    sid, tgt_channel, (handle, cmd, args) = mesg
    global CHANNEL, NICKS
    if (CHANNEL != tgt_channel and 'sysop' not in session.user.groups):
        return
    if cmd == 'join':
        if handle not in NICKS:
            NICKS[handle] = sid
            return show_join(handle, sid, tgt_channel)
    elif handle not in NICKS:
        NICKS[handle] = sid
    if cmd == 'part':
        if handle in NICKS:
            del NICKS[handle]
        return show_part(handle, sid, tgt_channel, args)
    elif cmd == 'say':
        return show_say(handle, args)
    elif cmd == 'act':
        return show_act(handle, args)
    else:
        return u'unhandled: %r' % (mesg,)
    return None


def show_act(handle, mesg):
    from x84.bbs import getsession, getterminal
    session, term = getsession(), getterminal()
    return u''.join((
        time.strftime('%H:%M'), u' * ',
        (term.bold_green(handle) if handle != session.handle
            else term.green(handle)), u' ',
        mesg,))


def show_join(handle, sid, chan):
    from x84.bbs import getsession, getterminal
    session, term = getsession(), getterminal()
    return u''.join((
        time.strftime('%H:%M'), u' ',
        term.blue('-'), u'!', term.blue('-'),
        u' ', term.bold_cyan(handle), u' ',
        (u''.join((term.bold_black('['),
            term.cyan(sid), term.bold_black(']'), u' ',))
            if 'sysop' in session.user.groups else u''),
        'has joined ',
        term.bold(chan),))


def show_part(handle, sid, chan, reason):
    from x84.bbs import getsession, getterminal
    session, term = getsession(), getterminal()
    return u''.join((
        time.strftime('%H:%M'), u' ',
        term.blue('-'), u'!', term.blue('-'),
        u' ', term.bold_cyan(handle), u' ',
        (u''.join((term.bold_black('['),
            term.cyan(sid), term.bold_black(']'), u' ',))
            if 'sysop' in session.user.groups else u''),
        'has left ',
        term.bold(chan),
        u' (%s)' % (reason,) if reason and 0 != len(reason) else u'',))

def show_whois(attrs):
    from x84.bbs import getsession, getterminal, timeago
    session, term = getsession(), getterminal()
    return u''.join((
        time.strftime('%H:%M'), u' ',
        term.blue('-'), u'!', term.blue('-'),
        u' ', term.bold(attrs['handle']), u' ',
        (u''.join((term.bold_black('['),
            term.cyan(attrs['sid']), term.bold_black(']'), u' ',))
            if 'sysop' in session.user.groups else u''), u'\n',
        time.strftime('%H:%M'), u' ',
        term.blue('-'), u'!', term.blue('-'),
        u' ', u'CONNECtED ',
        term.bold_cyan(timeago(time.time() - attrs['connect_time'])),
        ' AGO.', u'\n',
        time.strftime('%H:%M'), u' ',
        term.blue('-'), u'!', term.blue('-'),
        u' ', term.bold(u'idlE: '),
        term.bold_cyan(timeago(time.time() - attrs['idle'])), u'\n',
        ))

def show_nicks(handles):
    from x84.bbs import getterminal
    term = getterminal()
    return u''.join((
        time.strftime('%H:%M'), u' ',
        term.blue('-'), u'!', term.blue('-'),
        u' ', term.bold_cyan('%d' % (len(handles))), u' ',
        u'user%s: ' % (u's' if len(handles) > 1 else u''),
        u', '.join(handles) + u'\n',))

def show_say(handle, mesg):
    from x84.bbs import getsession, getterminal, get_user
    session, term = getsession(), getterminal()
    return u''.join((
        time.strftime('%H:%M'), u' ',
        term.bold_black(u'<'),
        (term.bold_red(u'@') if handle != 'anonymous'
            and 'sysop' in get_user(handle).groups
            else u''),
        (handle if handle != session.handle
            else term.bold(handle)),
        term.bold_black(u'>'), u' ',
        mesg,))

def get_inputbar(pager):
    from x84.bbs import getterminal, ScrollingEditor
    term = getterminal()
    width = pager.visible_width - 2
    yloc = (pager.yloc + pager.height) - 2
    xloc = pager.xloc + 2
    ibar = ScrollingEditor(width, yloc, xloc)
    ibar.enable_scrolling = True
    ibar.max_length = 512
    ibar.colors['highlight'] = term.cyan_reverse
    return ibar

def get_pager(pager=None):
    from x84.bbs import getterminal, Pager
    term = getterminal()
    height = (term.height - 4)
    width = int(term.width * .9)
    yloc = term.height - height - 1
    xloc = (term.width / 2) - (width / 2)
    content = pager and pager.content
    pager = Pager(height, width, yloc, xloc)
    pager.enable_scrolling = True
    pager.colors['border'] = term.cyan
    pager.glyphs['right-vert'] = u'|'
    pager.glyphs['left-vert'] = u'|'
    pager.glyphs['bot-horiz'] = u''
    if content:
        pager.update('\n'.join(content))
    return pager


def main(channel=None, caller=None):
    from x84.bbs import getsession, getterminal, getch, echo
    session, term = getsession(), getterminal()
    global CHANNEL, EXIT, NICKS
    CHANNEL = '#partyline' if channel is None else channel
    EXIT = False
    NICKS = dict()

    # sysop repy_to is -1 to force user, otherwise prompt
    if channel == session.sid and caller not in (-1, None):
        echo(u''.join((
            term.normal, u'\b',
            u'\r\n', term.clear_eol,
            u'\r\n', term.clear_eol,
            term.bold_green(u' ** '),
            caller,
            u' would like to chat, accept? ',
            term.bold(u'['),
            term.bold_green_underline(u'yn'),
            term.bold(u']'),
            )))
        while True:
            ch = getch()
            if str(ch).lower() == 'y':
                break
            elif str(ch).lower() == 'n':
                return False

    def refresh(pager, ipb, init=False):
        session.activity = 'Chatting in %s' % (
                CHANNEL if not CHANNEL.startswith('#')
                and not 'sysop' in session.user.groups
                else u'PRiVAtE ChANNEl',) if CHANNEL is not None else (
                        u'WAitiNG fOR ChAt')
        return u''.join((
            u''.join((u'\r\n', term.clear_eol,
                u'\r\n', term.clear_eol,
                term.bold_cyan(u'//'),
                u' CitZENS bANd'.center(term.width).rstrip(),
                term.clear_eol,
                (u'\r\n' + term.clear_eol) * (pager.height + 2),
                pager.border())) if init else u'',
            pager.title(u''.join((
                term.bold_cyan(u']- '),
                CHANNEL if CHANNEL is not None else u'',
                term.bold_cyan(u' -['),))),
            pager.refresh(),
            ipb.refresh(),))

    def cmd(pager, msg):
        cmd, args = msg.split()[0], msg.split()[1:]
        global CHANNEL, NICKS
        if cmd == '/help':
            pager.append(show_help())
            return True
        elif cmd == '/join' and len(args) == 1:
            part_chan('lEAViNG fOR ANOthER ChANNEl')
            CHANNEL = args[0]
            NICKS = dict()
            join_chan()
            return True
        elif cmd in ('/act', '/me',):
            act(u' '.join(args))
        elif cmd == '/say':
            say(u' '.join(args))
        elif cmd == '/part':
            part_chan(u' '.join(args))
            CHANNEL = None
            NICKS = dict()
            return True
        elif cmd == '/quit':
            part_chan('quit')
            global EXIT
            EXIT = True
        elif cmd == '/users':
            pager.append(show_nicks(NICKS.keys()))
            return True
        elif cmd == '/whois' and len(args) == 1:
            whois(args[0])
        return False

    def broadcast_cc(payload):
        session.send_event('global', ('chat', payload))
        session.buffer_event('global', ('chat', payload))

    def join_chan():
        payload = (session.sid, CHANNEL, (session.user.handle, 'join', None))
        broadcast_cc(payload)

    def say(mesg):
        payload = (session.sid, CHANNEL, (session.user.handle, 'say', mesg))
        broadcast_cc(payload)

    def act(mesg):
        payload = (session.sid, CHANNEL, (session.user.handle, 'act', mesg))
        broadcast_cc(payload)

    def part_chan(reason):
        payload = (session.sid, CHANNEL, (session.user.handle, 'part', reason))
        broadcast_cc(payload)

    def whois(handle):
        if not handle in NICKS:
            return
        session.send_event('route', (NICKS[handle], 'info-req', session.sid,))

    def whois_response(attrs):
        return show_whois(attrs)

    pager = get_pager(None)  # output window
    readline = get_inputbar(pager)  # input bar
    echo(refresh(pager, readline, init=True))
    dirty = time.time()
    join_chan()
    while not EXIT:
        inp = getch(POLL_KEY)

        # poll for and process screen resize
        if session.poll_event('refresh') or (
                inp in (term.KEY_REFRESH, unichr(12))):
            pager = get_pager(pager)
            saved_inp = readline.content
            readline = get_inputbar(pager)
            readline.content = saved_inp
            echo(refresh(pager, readline, init=True))
            dirty = None

        # poll for and process chat events,
        mesg = session.poll_event('global')
        if mesg is not None:
            otxt = process(mesg[1])
            if otxt is not None:
                echo(pager.append(otxt))
                dirty = None if dirty is None else time.time()

        # poll for whois response
        data = session.poll_event('info-ack')
        if data is not None:
            sid, attrs = data
            echo(pager.append(whois_response(attrs)))
            dirty = None if dirty is None else time.time()

        # process keystroke as input, or, failing that,
        # as a command key to the pager. refresh portions of
        # input bar or act on cariage return, accordingly.
        if inp in (term.KEY_EXIT, unichr(27)):
            return
        elif inp is not None:
            otxt = readline.process_keystroke(inp)
            if readline.carriage_returned:
                if readline.content.startswith('/'):
                    if cmd(pager, readline.content):
                        pager = get_pager(pager)
                        echo(refresh(pager, readline, init=True))
                elif (0 != len(readline.content.strip())
                        and CHANNEL is not None):
                    say(readline.content)
                readline = get_inputbar(pager)
                echo(readline.refresh())
            elif 0 == len(otxt):
                if type(inp) is int:
                    echo(pager.process_keystroke(inp))
            else:
                echo(u''.join((
                    readline.fixate(-1),
                    readline.colors.get('highlight', u''),
                    otxt, term.normal)))

        # update pager contents. Its a lot for 9600bps ..
        if dirty is not None and time.time() - dirty > POLL_OUT:
            echo(refresh(pager, readline))
            dirty = None