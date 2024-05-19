#!/bin/bash

# Function to convert a signed integer to its binary representation
to_binary() {
  local num=$1
  if (( num < 0 )); then
    # Convert negative number to its two's complement binary representation
    num=$(( (1 << 32) + num ))
  fi
  printf "%032d" "$(echo "obase=2; $num" | bc)"
}

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <square_from> <square_to>"
  exit 1
fi

square_from=$1
square_to=$2

# Convert arguments to binary
bin_square_from=$(to_binary $square_from)
bin_square_to=$(to_binary $square_to)

# Combine the binary representations
combined_command="$bin_square_from$bin_square_to"

# Loop through each bit in the combined command
for (( i=0; i<${#combined_command}; i++ )); do
  bit=${combined_command:$i:1}
  
  if [ "$bit" -eq "0" ]; then
    pinctrl set 17 dl
  else
    pinctrl set 17 dh
  fi
  
  pinctrl set 27 dh
  sleep 0.05
  pinctrl set 27 dl
  sleep 0.05
done
