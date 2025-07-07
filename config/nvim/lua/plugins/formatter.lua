return {
    'stevearc/conform.nvim',
    event = { 'BufWritePre' },
    cmd = { 'ConformInfo' },
    config = function()
        local conform = require('conform')

        conform.setup({
            formatters_by_ft = {
                lua = { 'stylua' },
                go = { 'gofmt', 'goimports' },
                rust = { 'rustfmt' },
                javascript = { 'prettier' },
                typescript = { 'prettier' },
                csharp = { 'csharpier' },
                json = { 'prettier' },
                yaml = { 'prettier' },
                html = { 'prettier' },
                css = { 'prettier' },
            },
            format_on_save = {
                timeout_ms = 500,
                lsp_fallback = true,
            },
        })

        vim.keymap.set({ 'n', 'v' }, '<leader>cf', function()
            conform.format({ async = true, lsp_fallback = true })
        end, { desc = 'Format file' })
    end,
}
