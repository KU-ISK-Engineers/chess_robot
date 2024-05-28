#!/bin/bash

root_dir="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

echo "Changing directory to project root"
cd $(echo $root_dir)

echo "Installing required libraries"
dpkg -s tk > /dev/null
if [ $? -ne 0 ]; then
    sudo apt-get install tk
fi

echo "Installing executable"
echo "#!/bin/bash" | sudo tee /usr/local/bin/chess2
echo "bash $root_dir/run.sh" | sudo tee --append /usr/local/bin/chess2

echo "Installing desktop icon"
cp  chess2.desktop ~/Desktop/
