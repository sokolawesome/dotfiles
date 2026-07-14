local huawei = "desc:Huawei Technologies Co. Inc. ZQE-CBA 0xC080F622"
local xiaomi = "desc:Xiaomi Corporation Mi Monitor 5640810077619"

hl.monitor({
    output = huawei,
    mode = "3440x1440@165.00",
    position = "2560x0",
    scale = 1,
    bitdepth = 10,
    cm = "dp3",
})
hl.monitor({ output = xiaomi, mode = "2560x1440@75", position = "0x0", scale = 1 })
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })

hl.workspace_rule({ workspace = "1", monitor = xiaomi, default = true })
hl.workspace_rule({ workspace = "2", monitor = xiaomi })
hl.workspace_rule({ workspace = "3", monitor = xiaomi })
hl.workspace_rule({ workspace = "4", monitor = xiaomi })
hl.workspace_rule({ workspace = "5", monitor = huawei, default = true })
hl.workspace_rule({ workspace = "6", monitor = huawei })
hl.workspace_rule({ workspace = "7", monitor = huawei })
hl.workspace_rule({ workspace = "8", monitor = huawei })
