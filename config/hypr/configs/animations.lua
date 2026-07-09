hl.config({
    animations = {
        enabled = true,
    },
})

hl.curve("easeInOutSine", { type = "bezier", points = { { 0.05, 0.6 }, { 0.05, 1 } } })

hl.animation({ leaf = "windows",    enabled = true, speed = 1, bezier = "easeInOutSine", style = "slide" })
hl.animation({ leaf = "fade",       enabled = true, speed = 1, bezier = "easeInOutSine" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 3, bezier = "easeInOutSine", style = "slide" })
hl.animation({ leaf = "layers",     enabled = true, speed = 1, bezier = "easeInOutSine", style = "slide" })
