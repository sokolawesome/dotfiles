local mainMod = "SUPER"

local function ipc(args)
    return hl.dsp.exec_cmd("qs -c noctalia-shell ipc call " .. args)
end

-- core binds
hl.bind(mainMod .. " + SPACE", ipc("controlCenter toggle"))
hl.bind(mainMod .. " + W", ipc("wallpaper toggle"))
hl.bind(mainMod .. " + comma", ipc("settings toggle"))
hl.bind(mainMod .. " + Escape", ipc("sessionMenu toggle"))

-- media keys
hl.bind("XF86AudioRaiseVolume", ipc("volume increase"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", ipc("volume decrease"), { locked = true, repeating = true })
hl.bind("XF86AudioMute", ipc("volume muteOutput"), { locked = true })
hl.bind("XF86MonBrightnessUp", ipc("brightness increase"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", ipc("brightness decrease"), { locked = true, repeating = true })

-- app launchers
hl.bind(mainMod .. " + Return", hl.dsp.exec_cmd("kitty"))
hl.bind(mainMod .. " + B", hl.dsp.exec_cmd("zen-browser"))
hl.bind(mainMod .. " + C", hl.dsp.exec_cmd("code"))
hl.bind(mainMod .. " + D", ipc("launcher toggle"))
hl.bind(mainMod .. " + SHIFT + D", ipc("launcher windows"))
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd("kitty -e yazi"))
hl.bind(mainMod .. " + T", hl.dsp.exec_cmd("Telegram"))
hl.bind(mainMod .. " + ALT + V", ipc("launcher clipboard"))

-- window actions
hl.bind(mainMod .. " + Q", hl.dsp.window.close())
hl.bind(mainMod .. " + F", hl.dsp.window.fullscreen({ mode = "fullscreen" }))
hl.bind(mainMod .. " + V", hl.dsp.window.float({ action = "toggle" }))

-- focus movement
hl.bind(mainMod .. " + left", hl.dsp.focus({ direction = "left" }))
hl.bind(mainMod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(mainMod .. " + up", hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + down", hl.dsp.focus({ direction = "down" }))

-- move window
hl.bind(mainMod .. " + SHIFT + left", hl.dsp.window.move({ direction = "left" }))
hl.bind(mainMod .. " + SHIFT + right", hl.dsp.window.move({ direction = "right" }))
hl.bind(mainMod .. " + SHIFT + up", hl.dsp.window.move({ direction = "up" }))
hl.bind(mainMod .. " + SHIFT + down", hl.dsp.window.move({ direction = "down" }))

-- resize window
hl.bind(mainMod .. " + CTRL + left", hl.dsp.window.resize({ x = -50, y = 0, relative = true }))
hl.bind(mainMod .. " + CTRL + right", hl.dsp.window.resize({ x = 50, y = 0, relative = true }))
hl.bind(mainMod .. " + CTRL + up", hl.dsp.window.resize({ x = 0, y = -50, relative = true }))
hl.bind(mainMod .. " + CTRL + down", hl.dsp.window.resize({ x = 0, y = 50, relative = true }))

-- switch to workspace / move window to workspace
for i = 1, 8 do
    hl.bind(mainMod .. " + " .. i, hl.dsp.focus({ workspace = i }))
    hl.bind(mainMod .. " + SHIFT + " .. i, hl.dsp.window.move({ workspace = i }))
end

-- workspace navigation
hl.bind(mainMod .. " + TAB", hl.dsp.focus({ workspace = "m+1" }))
hl.bind(mainMod .. " + SHIFT + TAB", hl.dsp.focus({ workspace = "m-1" }))
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up", hl.dsp.focus({ workspace = "e-1" }))

-- mouse interactions
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- scrolling layout
hl.bind(mainMod .. " + R", hl.dsp.layout("colresize +conf")) -- cycle column width (0.333 / 0.5 / 0.667 / 1.0)
hl.bind(mainMod .. " + bracketleft", hl.dsp.layout("move -col"))
hl.bind(mainMod .. " + bracketright", hl.dsp.layout("move +col"))
hl.bind(mainMod .. " + N", hl.dsp.layout("consume_or_expel next"))

-- media
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"), { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"), { locked = true })

-- screenshots
hl.bind(mainMod .. " + S", hl.dsp.exec_cmd([[bash -c 'region=$(slurp); sleep 0.25; [ -n "$region" ] && grim -g "$region" - | wl-copy']]))
hl.bind(mainMod .. " + CTRL + S", hl.dsp.exec_cmd([[bash -c 'region=$(slurp); sleep 0.25; [ -n "$region" ] && grim -g "$region" - | swappy -f -']]))
