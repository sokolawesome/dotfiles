return {
    'nvim-neo-tree/neo-tree.nvim',
    dependencies = {
        'nvim-lua/plenary.nvim',
        'nvim-tree/nvim-web-devicons',
        'MunifTanjim/nui.nvim',
    },
    config = function()
        vim.keymap.set('n', '<leader>fe', '<cmd>Neotree toggle<cr>', { desc = 'File explorer' })
    end,
}
