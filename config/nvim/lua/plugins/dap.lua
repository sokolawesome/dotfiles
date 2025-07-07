return {
    'mfussenegger/nvim-dap',
    dependencies = {
        {
            'rcarriga/nvim-dap-ui',
            dependencies = { 'nvim-neotest/nvim-nio' },
            config = function()
                local dapui = require('dapui')
                dapui.setup({
                    layouts = {
                        {
                            elements = {
                                { id = 'scopes',      size = 0.25 },
                                { id = 'breakpoints', size = 0.25 },
                                { id = 'stacks',      size = 0.25 },
                                { id = 'watches',     size = 0.25 },
                            },
                            size = 40,
                            position = 'left',
                        },
                        {
                            elements = {
                                { id = 'repl',    size = 0.5 },
                                { id = 'console', size = 0.5 },
                            },
                            size = 0.25,
                            position = 'bottom',
                        },
                    },
                })

                local dap = require('dap')
                dap.listeners.after.event_initialized['dapui_config'] = function()
                    dapui.open()
                end
                dap.listeners.before.event_terminated['dapui_config'] = function()
                    dapui.close()
                end
                dap.listeners.before.event_exited['dapui_config'] = function()
                    dapui.close()
                end
            end,
        },
        {
            'williamboman/mason.nvim',
            dependencies = { 'jay-babu/mason-nvim-dap.nvim' },
            config = function()
                require('mason-nvim-dap').setup({
                    ensure_installed = { 'delve' },
                    handlers = {},
                })
            end,
        },
    },
    config = function()
        local dap = require('dap')

        vim.keymap.set('n', '<leader>dt', function() dap.toggle_breakpoint() end, { desc = 'Toggle Breakpoint' })
        vim.keymap.set('n', '<leader>dc', function() dap.continue() end, { desc = 'Continue' })
        vim.keymap.set('n', '<leader>dj', function() dap.step_over() end, { desc = 'Step Over' })
        vim.keymap.set('n', '<leader>dk', function() dap.step_into() end, { desc = 'Step Into' })
        vim.keymap.set('n', '<leader>do', function() dap.step_out() end, { desc = 'Step Out' })
        vim.keymap.set('n', '<leader>du', function() require('dapui').toggle() end, { desc = 'Toggle DAP UI' })

        dap.adapters.delve = {
            type = 'server',
            port = '${port}',
            executable = {
                command = 'dlv',
                args = { 'dap', '-l', '127.0.0.1:${port}' },
            },
        }
        dap.configurations.go = {
            {
                type = 'delve',
                name = 'Debug',
                request = 'launch',
                program = '${file}',
            },
            {
                type = 'delve',
                name = 'Debug test',
                request = 'launch',
                mode = 'test',
                program = '${file}',
            },
        }
    end,
}
