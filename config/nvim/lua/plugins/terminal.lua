return {
    'akinsho/toggleterm.nvim',
    config = function()
        local toggleterm = require('toggleterm')

        toggleterm.setup({
            size = 20,
            open_mapping = [[<c-\>]],
            hide_numbers = true,
            shade_filetypes = {},
            shade_terminals = true,
            shading_factor = 2,
            start_in_insert = true,
            insert_mappings = true,
            persist_size = true,
            direction = 'float',
            close_on_exit = true,
            shell = vim.o.shell,
        })

        local Terminal = require('toggleterm.terminal').Terminal
        local lazygit = Terminal:new({
            cmd = 'lazygit',
            hidden = true,
            direction = 'float',
            float_opts = {
                border = 'double',
            },
        })

        function _LAZYGIT_TOGGLE()
            lazygit:toggle()
        end

        vim.keymap.set('n', '<leader>gg', '<cmd>lua _LAZYGIT_TOGGLE()<CR>', {
            noremap = true,
            silent = true,
            desc = 'Toggle LazyGit',
        })
    end,
}
