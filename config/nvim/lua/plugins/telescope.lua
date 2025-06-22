return {
    "nvim-telescope/telescope.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    config = function()
        local telescope = require("telescope")
        telescope.setup({
            defaults = {
                layout_strategy = "horizontal",
                layout_config = {
                    preview_cutoff = 100,
                    horizontal = {
                        preview_width = 0.6,
                    },
                },
            },
        })
    end,
}
