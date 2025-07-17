return {
    "Exafunction/windsurf.nvim",
    dependencies = {
        "nvim-lua/plenary.nvim",
        "hrsh7th/nvim-cmp",
    },
    config = function()
        require("codeium").setup({
            enable_cmp_source = false,
            virtual_text = {
                enabled = true,
                idle_delay = 400,
            }
        })
    end,
}
