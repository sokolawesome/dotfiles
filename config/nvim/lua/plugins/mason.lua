return {
    'williamboman/mason.nvim',
    dependencies = {
        'williamboman/mason-lspconfig.nvim',
        'neovim/nvim-lspconfig',
    },
    config = function()
        local mason = require('mason')
        local mason_lspconfig = require('mason-lspconfig')
        local lspconfig = require('lspconfig')
        local lsp_defaults = require('plugins.lsp')
        local capabilities = require('cmp_nvim_lsp').default_capabilities()

        mason.setup()

        mason_lspconfig.setup({
            ensure_installed = {
                'gopls',
                -- 'rust_analyzer',
                -- 'tsserver',
                -- 'csharp_ls',
                -- 'html',
                -- 'cssls',
                -- 'yamlls',
                -- 'jsonls',
            },
            handlers = {
                function(server_name)
                    lspconfig[server_name].setup({
                        on_attach = lsp_defaults.on_attach,
                        capabilities = capabilities,
                    })
                end,

                ['gopls'] = function()
                    lspconfig.gopls.setup({
                        on_attach = lsp_defaults.on_attach,
                        capabilities = capabilities,
                        settings = {
                            gopls = {
                                analyses = {
                                    unusedparams = true,
                                },
                                staticcheck = true,
                            },
                        },
                    })
                end,
            },
        })
    end,
}
