hl.config({
    animations = {
        enabled = true,
    },
})

hl.curve("quick", { type = "bezier", points = { { 0.15, 0 }, { 0.1, 1 } } })

hl.animation({ leaf = "windows",    enabled = true, speed = 1.5, bezier = "quick", style = "popin 90%" })
hl.animation({ leaf = "fade",       enabled = true, speed = 1.2, bezier = "quick" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 1.5, bezier = "quick", style = "slidefade 15%" })
hl.animation({ leaf = "layers",     enabled = true, speed = 1.5, bezier = "quick", style = "slide" })
