return {
    'stevearc/conform.nvim',
    event = { 'BufWritePre', 'BufNewFile', 'BufReadPre' },
    cmd = { 'ConformInfo' },
    config = function()
        local conform = require('conform')

        conform.setup({
            formatters_by_ft = {
                lua = { 'stylua' },
                go = { 'gofmt', 'goimports' },
                rust = { 'rustfmt' },
                csharp = { 'csharpier' },
                bash = { 'shfmt' },

                javascript = { 'prettier' },
                typescript = { 'prettier' },
                json = { 'prettier' },
                yaml = { 'prettier' },
                html = { 'prettier' },
                css = { 'prettier' },
            },
            format_on_save = {
                async = false,
                timeout_ms = 1000,
                lsp_fallback = true,
            },
        })

        vim.keymap.set({ 'n', 'v' }, '<leader>cf', function()
            conform.format({ async = false, timeout_ms = 1000, lsp_fallback = true })
        end, { desc = 'Format file' })
    end,
}
