return {
    "folke/which-key.nvim",
    event = "VeryLazy",
    config = function()
        local wk = require("which-key")

        wk.setup({
            preset = "modern",
            delay = 200,
            expand = 1,
            notify = true,
            replace = {
                ["<space>"] = "SPC",
                ["<cr>"] = "RET",
                ["<tab>"] = "TAB",
            },
        })

        wk.add({
            -- File operations
            { "<leader>f",  group = "Find" },
            { "<leader>ff", desc = "Find Files" },
            { "<leader>fg", desc = "Live Grep" },
            { "<leader>fb", desc = "Buffers" },
            { "<leader>fh", desc = "Help Tags" },
            { "<leader>fr", desc = "Recent Files" },

            -- File explorer
            { "<leader>e",  group = "Explorer" },
            { "<leader>e",  desc = "Toggle Tree" },
            { "<leader>ef", desc = "Focus Tree" },

            -- Buffer management
            { "<leader>b",  group = "Buffer" },
            { "<leader>bn", desc = "Next Buffer" },
            { "<leader>bp", desc = "Previous Buffer" },
            { "<leader>bd", desc = "Delete Buffer" },

            -- Window management
            { "<leader>s",  group = "Split" },
            { "<leader>sv", desc = "Vertical Split" },
            { "<leader>sh", desc = "Horizontal Split" },
            { "<leader>sc", desc = "Close Split" },

            -- Code operations (LSP)
            { "<leader>c",  group = "Code" },
            { "<leader>ca", desc = "Code Action" },
            { "<leader>cf", desc = "Format" },
            { "<leader>rn", desc = "Rename" },

            -- Diagnostics
            { "<leader>d",  group = "Diagnostics" },
            { "<leader>dn", desc = "Next Diagnostic" },
            { "<leader>dp", desc = "Previous Diagnostic" },
            { "<leader>df", desc = "Diagnostic Float" },
            { "<leader>dl", desc = "Diagnostic List" },

            -- Quick fix
            { "<leader>q",  group = "Quick Fix" },
            { "<leader>qo", desc = "Open Quickfix" },
            { "<leader>qc", desc = "Close Quickfix" },
            { "<leader>qn", desc = "Next Quickfix" },
            { "<leader>qp", desc = "Previous Quickfix" },

            -- Terminal
            { "<leader>t",  desc = "Toggle Terminal" },

            -- Basic operations
            { "<leader>w",  desc = "Save File" },
            { "<leader>q",  desc = "Quit" },
            { "<leader>x",  desc = "Save and Quit" },

            -- Navigation hints
            { "g",          group = "Go to" },
            { "gd",         desc = "Go to Definition" },
            { "gD",         desc = "Go to Declaration" },
            { "gi",         desc = "Go to Implementation" },
            { "gr",         desc = "Go to References" },
        })

        -- Show cheatsheet with <leader>?
        vim.keymap.set("n", "<leader>?", function()
            wk.show({ global = true })
        end, { desc = "Show All Keymaps" })
    end,
}
