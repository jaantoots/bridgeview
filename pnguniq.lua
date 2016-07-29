local argparse = require "argparse"
local gm = require "graphicsmagick"

local parser = argparse("pnguniq.lua", "Return unique colors in a PNG image.")
parser:argument("file", "PNG file to check.")
local args = parser:parse()

local function bytesToHex (bytes)
  -- body...
  return string.format('#%02x%02x%02x', bytes[1], bytes[2], bytes[3])
end

local img = gm.Image(args.file):toTensor('byte')
local size = img:size()
local colors = {}
for i=1,size[1] do
  -- body...
  for j=1,size[2] do
    -- body...
    colors[bytesToHex(img[i][j])] = true
  end
end

for color,_ in pairs(colors) do
  -- body...
  print(color)
end
