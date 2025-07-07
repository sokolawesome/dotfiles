return {
    'mfussenegger/nvim-lint',
    event = {
        'BufReadPre',
        'BufNewFile',
    },
    config = function()
        local lint = require('lint')

        lint.linters_by_ft = {
            go = { 'golangcilint' },
            yaml = { 'yamllint' },
            json = { 'jsonlint' },
            shell = { 'shellcheck' },
            javascript = { "eslint_d" },
            typescript = { "eslint_d" },
            javascriptreact = { "eslint_d" },
            typescriptreact = { "eslint_d" },
        }

        vim.api.nvim_create_autocmd({ 'BufWritePost', 'BufEnter', 'InsertLeave' }, {
            group = vim.api.nvim_create_augroup('nvim-lint', { clear = true }),
            callback = function()
                lint.try_lint()
            end,
        })

        vim.keymap.set({ 'n', 'v' }, "<leader>cl", function()
            lint.try_lint()
        end, { desc = "Lint file" })
    end,
}
