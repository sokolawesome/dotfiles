return {
    'goolord/alpha-nvim',
    event = "VimEnter",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    config = function()
        local alpha = require("alpha")
        local dashboard = require("alpha.themes.dashboard")
        dashboard.section.header.val = {
            ".._____...____...__...__......_..._......_......____....____....",
            ".|_..._|.|.._.\\..\\.\\././.....|.|.|.|..../.\\....|.._.\\..|.._.\\...",
            "...|.|...|.|_).|..\\.V./......|.|_|.|.../._.\\...|.|_).|.|.|.|.|..",
            "...|.|...|.._.<....|.|.......|.._..|../.___.\\..|.._.<..|.|_|.|..",
            "...|_|...|_|.\\_\\...|_|.......|_|.|_|./_/...\\_\\.|_|.\\_\\.|____/...",
            "................................................................",
            "............_____....___....____......._.....__...__............",
            "...........|_..._|../._.\\..|.._.\\...../.\\....\\.\\././............",
            ".............|.|...|.|.|.|.|.|.|.|.../._.\\....\\.V./.............",
            ".............|.|...|.|_|.|.|.|_|.|../.___.\\....|.|..............",
            ".............|_|....\\___/..|____/../_/...\\_\\...|_|..............",
            "................................................................",
        }
        dashboard.section.buttons.val = {
            dashboard.button("f", "󰥨  Find File", "<cmd>Telescope find_files<cr>"),
            dashboard.button("r", "󰪺  Recent Files", "<cmd>Telescope oldfiles<cr>"),
            dashboard.button("p", "󰚝  Projects", "<cmd>Telescope projects<cr>"),
            dashboard.button("c", "  Config", "<cmd>e $MYVIMRC<cr>"),
            dashboard.button("q", "󱎘  Quit", "<cmd>qa<cr>"),
        }
        alpha.setup(dashboard.opts)

        vim.api.nvim_create_autocmd("User", {
            once = true,
            pattern = "LazyVimStarted",
            callback = function()
                local stats = require("lazy").stats()
                local ms = (math.floor(stats.startuptime * 100 + 0.5) / 100)
                dashboard.section.footer.val = "⚡ Neovim loaded "
                    .. stats.loaded
                    .. "/"
                    .. stats.count
                    .. " plugins in "
                    .. ms
                    .. "ms"
                pcall(vim.cmd.AlphaRedraw)
            end,
        })
    end
};
