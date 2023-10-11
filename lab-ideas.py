def shift_polygon_coordinates(coordinates):
    """
    Shift the coordinates of a polygon by replacing the first pair with the second and closing the polygon.

    Parameters:
        coordinates (list): List of tuples representing the coordinates (x, y) of the polygon.

    Returns:
        list: New list of shifted coordinates.
    """

    if len(coordinates) < 3:
        return "A valid polygon must have at least 3 coordinates."

    # Remove the first coordinate
    shifted_coordinates = coordinates[1:]

    # Add the second coordinate to the end to close the polygon
    shifted_coordinates.append(coordinates[1])

    return shifted_coordinates


def shift_polygon_coordinates_reverse(coordinates):
    """
    Shift and close the coordinates of a polygon by moving the last coordinate to the beginning and adding the penultimate coordinate to the beginning.

    Parameters:
        coordinates (list): List of tuples representing the coordinates (x, y) of the polygon.

    Returns:
        list: New list of shifted and closed coordinates.
    """

    if len(coordinates) < 3:
        return "A valid polygon must have at least 3 coordinates."

    # Move the last coordinate to the beginning
    shifted_coordinates = coordinates[:-1]

    # Add the penultimate coordinate (which is now the second in the shifted list) to the beginning to close the polygon
    shifted_coordinates.insert(0, coordinates[-2])

    return shifted_coordinates


# Example usage
if __name__ == "__main__":
    original_coordinates = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
    new_coordinates = shift_polygon_coordinates(original_coordinates)
    new_coordinates_reverse = shift_polygon_coordinates_reverse(original_coordinates)

    print("Original coordinates:", original_coordinates)
    print("Shifted coordinates:", new_coordinates)
    print("Shifted coordinates reverse:", new_coordinates_reverse)

