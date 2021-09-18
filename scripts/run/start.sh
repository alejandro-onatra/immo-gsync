root_folder=$( cd ../../ && pwd )

# Check PYTHONPATH
echo "Found that the PYTHON path is [${PYTHONPATH}]"
if [ -z "$PYTHONPATH"  ]; then
    export PYTHONPATH="${root_folder}"
    echo "Now the python path is [${PYTHONPATH}]"
fi

# Load the properties file
properties_file="${root_folder}/environment/production.properties"
if [ -f "$properties_file" ]; then
  echo "$properties_file found."
  while IFS=':=' read -r key value; do
    key=$(echo $key | tr '.' '_')
    export "${key}${value}"
  done < "$properties_file"
else
  echo "$properties_file not found."
  echo "Using the environmental variables given in the container"
fi

# Schedule script
src_folder="$(cd ../../ && pwd)/src/"
main_name="main.py"
script_path="${src_folder}${main_name}"
echo "The script path is ${script_path}"
python3 ${script_path}
