local keymap = vim.keymap.set
local opts = { noremap = true, silent = true }

-- Basic editing
keymap("n", "<leader>w", ":w<CR>", opts)
keymap("n", "<leader>q", ":q<CR>", opts)
keymap("n", "<leader>x", ":x<CR>", opts)
keymap("n", "<Esc>", ":noh<CR>", opts)

-- Window management
keymap("n", "<leader>sv", ":vsplit<CR>", opts)
keymap("n", "<leader>sh", ":split<CR>", opts)
keymap("n", "<leader>sc", ":close<CR>", opts)
keymap("n", "<C-h>", "<C-w>h", opts)
keymap("n", "<C-j>", "<C-w>j", opts)
keymap("n", "<C-k>", "<C-w>k", opts)
keymap("n", "<C-l>", "<C-w>l", opts)

-- Buffer management
keymap("n", "<leader>bn", ":bnext<CR>", opts)
keymap("n", "<leader>bp", ":bprev<CR>", opts)
keymap("n", "<leader>bd", ":bdelete<CR>", opts)

-- Text manipulation
keymap("v", "J", ":m '>+1<CR>gv=gv", opts)
keymap("v", "K", ":m '<-2<CR>gv=gv", opts)
keymap("n", "J", "mzJ`z", opts)
keymap("n", "<C-d>", "<C-d>zz", opts)
keymap("n", "<C-u>", "<C-u>zz", opts)

-- Search improvements
keymap("n", "n", "nzzzv", opts)
keymap("n", "N", "Nzzzv", opts)

-- File operations
keymap("n", "<leader>ff", ":Telescope find_files<CR>", opts)
keymap("n", "<leader>fg", ":Telescope live_grep<CR>", opts)
keymap("n", "<leader>fb", ":Telescope buffers<CR>", opts)
keymap("n", "<leader>fh", ":Telescope help_tags<CR>", opts)
keymap("n", "<leader>fr", ":Telescope oldfiles<CR>", opts)

-- File explorer
keymap("n", "<leader>e", ":NvimTreeToggle<CR>", opts)
keymap("n", "<leader>ef", ":NvimTreeFocus<CR>", opts)

-- LSP keymaps
local function lsp_keymaps(bufnr)
    local lsp_opts = { buffer = bufnr, noremap = true, silent = true }

    keymap("n", "gd", vim.lsp.buf.definition, lsp_opts)
    keymap("n", "gD", vim.lsp.buf.declaration, lsp_opts)
    keymap("n", "gi", vim.lsp.buf.implementation, lsp_opts)
    keymap("n", "gr", vim.lsp.buf.references, lsp_opts)
    keymap("n", "K", vim.lsp.buf.hover, lsp_opts)
    keymap("n", "<C-k>", vim.lsp.buf.signature_help, lsp_opts)

    keymap("n", "<leader>rn", vim.lsp.buf.rename, lsp_opts)
    keymap("n", "<leader>ca", vim.lsp.buf.code_action, lsp_opts)
    keymap("n", "<leader>cf", vim.lsp.buf.format, lsp_opts)

    keymap("n", "<leader>dn", vim.diagnostic.goto_next, lsp_opts)
    keymap("n", "<leader>dp", vim.diagnostic.goto_prev, lsp_opts)
    keymap("n", "<leader>df", vim.diagnostic.open_float, lsp_opts)
    keymap("n", "<leader>dl", vim.diagnostic.setloclist, lsp_opts)
end

-- Terminal
keymap("n", "<leader>t", ":ToggleTerm<CR>", opts)
keymap("t", "<Esc>", "<C-\\><C-n>", opts)

-- Quick fix
keymap("n", "<leader>qo", ":copen<CR>", opts)
keymap("n", "<leader>qc", ":cclose<CR>", opts)
keymap("n", "<leader>qn", ":cnext<CR>", opts)
keymap("n", "<leader>qp", ":cprev<CR>", opts)

return {
    lsp_keymaps = lsp_keymaps,
}
