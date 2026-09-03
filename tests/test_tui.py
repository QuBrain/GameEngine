"""Test for NuclearSearchApp TUI workflow and rendering."""

import pytest
from nuclear_engine.tui import NuclearSearchApp


@pytest.mark.asyncio
async def test_tui_search_aircraft():
    app = NuclearSearchApp()
    async with app.run_test() as pilot:
        await pilot.press(*"Aircraft", "enter")
        await pilot.pause()
        content_display = app.query_one("#content_display")
        assert content_display is not None


@pytest.mark.asyncio
async def test_tui_search_method():
    app = NuclearSearchApp()
    async with app.run_test() as pilot:
        await pilot.press(*"Aircraft.LockedByMissile", "enter")
        await pilot.pause()
        content_display = app.query_one("#content_display")
        assert content_display is not None
