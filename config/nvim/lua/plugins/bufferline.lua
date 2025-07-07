return {
    'akinsho/bufferline.nvim',
    dependencies = { 'nvim-tree/nvim-web-devicons' },
    version = "*",
    config = function()
        require('bufferline').setup {
            options = {
                diagnostics = 'nvim_lsp',
                show_buffer_close_icons = true,
                show_close_icon = true,
            },
        }
        vim.keymap.set('n', '<Tab>', '<Cmd>BufferLineCycleNext<CR>', { desc = 'Next buffer' })
        vim.keymap.set('n', '<S-Tab>', '<Cmd>BufferLineCyclePrev<CR>', { desc = 'Previous buffer' })
        vim.keymap.set('n', '<leader>bd', '<Cmd>bdelete<CR>', { desc = 'Close buffer' })
    end,
}
