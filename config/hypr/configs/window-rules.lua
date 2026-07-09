-------------------------------
--    general window rules    --
-------------------------------

-- prevent windows from being automatically maximized
-- hl.window_rule({ match = { class = ".*" }, suppress_event = "maximize" })
-- ignore focus for unnamed or background xwayland windows
-- hl.window_rule({
--     match = { class = "^$", title = "^$", xwayland = true, float = true, fullscreen = false, pin = false },
--     no_focus = true,
-- })

-------------------------------
--   workspace assignments   --
-------------------------------

-- browsers
hl.window_rule({ match = { class = "zen" }, workspace = "5 silent" })
hl.window_rule({ match = { class = "chromium" }, workspace = "5 silent" })

-- messaging apps
hl.window_rule({ match = { class = "org.telegram.desktop" }, workspace = "4 silent" })

-------------------------------
--       floating tools      --
-------------------------------

hl.window_rule({ match = { class = "blueman-manager" }, float = true })

hl.window_rule({
    name = "pulseaudio-rule",
    match = { class = "org.pulseaudio.pavucontrol" },
    float = true,
    size = { "monitor_w*0.25", "monitor_h*0.75" },
    move = { "(monitor_w)", 40 },
})

hl.window_rule({
    name = "pip-rule",
    match = { title = "Picture-in-Picture" },
    float = true,
    pin = true,
    size = { 1024, 720 },
})

hl.window_rule({
    name = "file-chooser-rule",
    match = { class = "xdg-desktop-portal-gtk" },
    float = true,
    center = true,
    size = { "monitor_w/2", "monitor_h/2" },
})

hl.window_rule({
    name = "steam-rule",
    match = { initial_class = "steam" },
    workspace = "7",
    no_initial_focus = true,
})

hl.window_rule({
    name = "steam-updater-rule",
    match = { title = "Steam", class = "^$" },
    workspace = "7",
    no_initial_focus = true,
})

hl.window_rule({
    name = "steam-app-rule",
    match = { initial_class = "steam_app_" },
    workspace = "8",
    immediate = true,
})

hl.window_rule({
    name = "steam-friends-list-rule",
    match = { initial_title = "Friends List" },
    float = true,
    center = true,
    size = { 300, "monitor_h*0.6" },
})

hl.window_rule({
    name = "steam-settings-rule",
    match = { initial_title = "Steam Settings" },
    float = true,
    center = true,
    size = { "monitor_w/2", "monitor_h/2" },
})

hl.window_rule({
    name = "steam-browser-rule",
    match = { initial_title = "Steam - Browser" },
    float = true,
    center = true,
    size = { "monitor_w*0.8", "monitor_h*0.8" },
})
