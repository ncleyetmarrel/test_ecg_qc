from src.domain.data_reader import read_mit_bih_noise


def test_read_mit_bih_noise_should_return_a_generator():
    # Given
    snr = "e06"
    data_path = "tests/data_test/"
    expected_result_values = 2

    # When
    actual_result = read_mit_bih_noise(snr, data_path)
    counter = sum(1 for element in actual_result)

    # Then
    assert counter == expected_result_values


def test_read_mit_bih_noise_should_throw_an_exception_when_path_is_not_correct():
    pass
