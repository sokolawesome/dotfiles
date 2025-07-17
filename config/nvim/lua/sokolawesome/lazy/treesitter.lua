return {
    'nvim-treesitter/nvim-treesitter',
    build = ':TSUpdate',
    config = function()
        require('nvim-treesitter.configs').setup {
            ensure_installed = {
                'c_sharp',
                'go',
                'rust',
                'javascript',
                'typescript',
                'html',
                'css',
                'lua',
                'vim',
                'vimdoc',
                'query',
                'json',
                'yaml',
                'toml',
            },
            sync_install = false,
            auto_install = true,
            highlight = {
                enable = true,
                additional_vim_regex_highlighting = false,
            },
            indent = {
                enable = true
            },
        }
    end,
}
