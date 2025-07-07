return {
    'neovim/nvim-lspconfig',
    dependencies = {
        'williamboman/mason.nvim',
        'hrsh7th/cmp-nvim-lsp',
    },
    config = function()
        local M = {}

        M.on_attach = function(client, bufnr)
            local opts = { buffer = bufnr, remap = false }

            vim.keymap.set('n', 'gd', vim.lsp.buf.definition, opts)
            vim.keymap.set('n', 'K', vim.lsp.buf.hover, opts)
            vim.keymap.set('n', '<leader>ws', vim.lsp.buf.workspace_symbol, opts)
            vim.keymap.set('n', '<leader>vd', vim.diagnostic.open_float, opts)
            vim.keymap.set('n', '[d', vim.diagnostic.goto_next, opts)
            vim.keymap.set('n', ']d', vim.diagnostic.goto_prev, opts)
            vim.keymap.set('n', '<leader>ca', vim.lsp.buf.code_action, opts)
            vim.keymap.set('n', '<leader>rr', vim.lsp.buf.references, opts)
            vim.keymap.set('n', '<leader>rn', vim.lsp.buf.rename, opts)
            vim.keymap.set('i', '<C-h>', vim.lsp.buf.signature_help, opts)
        end

        return M
    end,
}
