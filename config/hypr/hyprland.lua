require("configs.variables")
require("configs.monitors")
require("configs.input")
require("configs.decorations")
require("configs.layout")
require("configs.animations")
require("configs.keybinds")
require("configs.window-rules")
require("configs.autostart")

-- noctalia color template renders ~/.config/hypr/noctalia.lua
-- the literal require("noctalia") below is what its apply script greps for
local ok, noctalia = pcall(require, "noctalia")
if ok then
    noctalia.apply_theme()
end
