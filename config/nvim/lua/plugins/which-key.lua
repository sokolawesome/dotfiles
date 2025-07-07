return {
    'folke/which-key.nvim',
    event = 'VeryLazy',
    config = function()
        local wk = require('which-key')
        wk.setup({
            preset = "modern",
            delay = 200,
            expand = 1,
            notify = true,
            replace = {
                ["<space>"] = "SPC",
                ["<cr>"] = "RET",
                ["<tab>"] = "TAB",
            },
        })

        wk.add({
            { '<leader>b',  group = '[B]uffer' },
            { '<leader>c',  group = '[C]ode' },
            { '<leader>ca', desc = 'Code Actions' },
            { '<leader>cf', desc = 'Format Code' },
            { '<leader>D',  group = '[D]ebug' },
            { '<leader>d',  group = '[D]iagnostic' },
            { '<leader>f',  group = '[F]ind' },
            { '<leader>fe', desc = 'File Explorer' },
            { '<leader>g',  group = '[G]it' },
            { '<leader>gg', desc = 'Toggle LazyGit' },
            { '<leader>r',  group = '[R]ename/[R]eferences' },
            { '<leader>rn', desc = 'Rename Symbol' },
            { '<leader>rr', desc = 'Find References' },
            { '<leader>w',  group = '[W]orkspace' },
            { '<leader>ws', desc = 'Workspace Symbols' },
        })
    end,
}
