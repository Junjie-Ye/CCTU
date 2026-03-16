set -e

thinking=false
overload=false
detail=false

while [[ "$1" != "" ]]; do
    case $1 in
        --model )
            shift
            model=$1
            ;;
        --user )
            shift
            user=$1
            ;;
        --api_key )
            shift
            api_key=$1
            ;;
        --base_url )
            shift
            base_url=$1
            ;;
        --input_dir )
            shift
            input_dir=$1
            ;;
        --output_dir )
            shift
            output_dir=$1
            ;;
        --repeat )
            shift
            repeat=$1
            ;;
        --max_workers )
            shift
            max_workers=$1
            ;;
        --max_retiries )
            shift
            max_retiries=$1
            ;;
        --start_id )
            shift
            start_id=$1
            ;;
        --end_id )
            shift
            end_id=$1
            ;;
        # -------- bool flags --------
        --thinking )
            thinking=true
            ;;
        --overload )
            overload=true
            ;;
        --detail )
            detail=true
            ;;
        * )
            echo "Unknown argument $1"
            exit 1
            ;;
    esac
    shift
done

PY_ARGS=()

[[ -n "$model" ]] && PY_ARGS+=(--model "$model")
[[ -n "$user" ]] && PY_ARGS+=(--user "$user")
[[ -n "$api_key" ]] && PY_ARGS+=(--api_key "$api_key")
[[ -n "$base_url" ]] && PY_ARGS+=(--base_url "$base_url")
[[ -n "$input_dir" ]] && PY_ARGS+=(--input_dir "$input_dir")
[[ -n "$output_dir" ]] && PY_ARGS+=(--output_dir "$output_dir")
[[ -n "$repeat" ]] && PY_ARGS+=(--repeat "$repeat")
[[ -n "$max_workers" ]] && PY_ARGS+=(--max_workers "$max_workers")

$thinking && PY_ARGS+=(--thinking)

printf 'Running: python response_generator.py'
printf ' %q' "${PY_ARGS[@]}"
printf '\n'

python response_generator.py "${PY_ARGS[@]}"

EVAL_ARGS=()

[[ -n "$input_dir" ]] && EVAL_ARGS+=(--input_dir "$input_dir")
[[ -n "$output_dir" ]] && EVAL_ARGS+=(--input_response_data "$output_dir/response.jsonl")
[[ -n "$output_dir" ]] && EVAL_ARGS+=(--output_file "$output_dir/eval_result.json")
[[ -n "$repeat" ]] && PY_ARGS+=(--repeat "$repeat")

$overload && EVAL_ARGS+=(--overload)
$detail && EVAL_ARGS+=(--detail)

python evaluation.py "${EVAL_ARGS[@]}"
